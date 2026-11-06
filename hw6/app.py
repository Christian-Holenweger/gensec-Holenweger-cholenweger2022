"""A small local password manager protected by a master password."""

import base64
import getpass
import os
import secrets
import sqlite3
import string
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


DATABASE_FILE = Path(__file__).with_name("passwords.db")
SALT_SIZE = 16
VERIFICATION_TEXT = b"Secure Password Manager key check"
MAX_ACCOUNT_LENGTH = 100
MAX_USERNAME_LENGTH = 100
WEAK_MASTER_PASSWORDS = {"123", "password", "admin123"}


def connect_database():
    """Open the database and create missing tables in the original format."""
    old_umask = os.umask(0o077)
    try:
        connection = sqlite3.connect(DATABASE_FILE)
    finally:
        os.umask(old_umask)
    tables = {row[0] for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = ?", ("table",)
    )}
    if "settings" not in tables:
        connection.execute(
            "CREATE TABLE settings (name TEXT PRIMARY KEY, value BLOB NOT NULL)"
        )
    if "credentials" not in tables:
        connection.execute(
            """CREATE TABLE credentials (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   account TEXT NOT NULL,
                   username TEXT NOT NULL,
                   encrypted_password BLOB NOT NULL
               )"""
        )
    connection.commit()
    return connection


def schema_columns(connection, table):
    """Return column names for a known application table."""
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def credential_password_column(connection):
    columns = schema_columns(connection, "credentials")
    if "encrypted_password" in columns:
        return "encrypted_password"
    if "password" in columns:
        return "password"
    raise sqlite3.DatabaseError("Credentials table has no encrypted password column.")


def derive_key(master_password, salt):
    """Derive a Fernet-compatible key from the master password and salt."""
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    raw_key = kdf.derive(master_password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def unlock(connection):
    """Create the first master password, or verify an existing one."""
    columns = schema_columns(connection, "settings")
    legacy_settings = {"name", "value"}.issubset(columns)
    if legacy_settings:
        values = dict(connection.execute(
            "SELECT name, value FROM settings WHERE name IN (?, ?)",
            ("salt", "verifier"),
        ).fetchall())
        salt, verification = values.get("salt"), values.get("verifier")
        initialized = salt is not None or verification is not None
    elif {"id", "salt", "verification"}.issubset(columns):
        row = connection.execute(
            "SELECT salt, verification FROM settings WHERE id = ?", (1,)
        ).fetchone()
        salt, verification = row if row else (None, None)
        initialized = row is not None
    else:
        raise sqlite3.DatabaseError("Unrecognized settings table format.")

    if not initialized:
        print("Create a master password. You will need it to access your vault.")
        while True:
            master = getpass.getpass("New master password: ")
            if len(master) < 12:
                print("The master password must be at least 12 characters long.")
                continue
            if master.strip().casefold() in WEAK_MASTER_PASSWORDS:
                print("Choose a less common master password.")
                continue
            confirmation = getpass.getpass("Confirm master password: ")
            if master != confirmation:
                print("Passwords do not match. Try again.")
                continue
            salt = secrets.token_bytes(SALT_SIZE)
            cipher = Fernet(derive_key(master, salt))
            if legacy_settings:
                connection.executemany(
                    "INSERT INTO settings (name, value) VALUES (?, ?)",
                    (("salt", salt), ("verifier", cipher.encrypt(VERIFICATION_TEXT))),
                )
            else:
                connection.execute(
                    "INSERT INTO settings (id, salt, verification) VALUES (?, ?, ?)",
                    (1, salt, cipher.encrypt(VERIFICATION_TEXT)),
                )
            connection.commit()
            return cipher

    if salt is None or verification is None:
        raise sqlite3.DatabaseError("The database is missing its password verifier.")
    for _ in range(3):
        master = getpass.getpass("Master password: ")
        try:
            cipher = Fernet(derive_key(master, salt))
            if cipher.decrypt(verification) == VERIFICATION_TEXT:
                return cipher
        except (InvalidToken, ValueError):
            pass
        print("Incorrect master password.")
    return None


def prompt_limited(label, max_length):
    """Ask for non-blank input that fits the field's size limit."""
    while True:
        value = input(label).strip()
        if not value:
            print("Please enter a value.")
        elif len(value) > max_length:
            print(f"Please use no more than {max_length} characters.")
        else:
            return value


def add_credential(connection, cipher):
    """Collect and save one encrypted credential."""
    account = prompt_limited("Account or website: ", MAX_ACCOUNT_LENGTH)
    username = prompt_limited("Username: ", MAX_USERNAME_LENGTH)
    password = getpass.getpass("Password to store (input hidden): ")
    if not password:
        print("Password cannot be empty; credential was not saved.")
        return
    column = credential_password_column(connection)
    connection.execute(
        f"INSERT INTO credentials (account, username, {column}) VALUES (?, ?, ?)",
        (account, username, cipher.encrypt(password.encode("utf-8"))),
    )
    connection.commit()
    print("Credential saved.")


def list_accounts(connection):
    """Display account names and usernames without revealing passwords."""
    rows = connection.execute(
        "SELECT id, account, username FROM credentials ORDER BY account, id"
    ).fetchall()
    if not rows:
        print("No credentials saved yet.")
        return
    print("\nSaved accounts:")
    for credential_id, account, username in rows:
        print(f"{credential_id}. {account} — {username}")


def choose_credential(connection, action):
    """Find a credential by numeric ID or account name."""
    rows = connection.execute(
        "SELECT id, account, username FROM credentials ORDER BY account, id"
    ).fetchall()
    if not rows:
        print("No credentials saved yet.")
        return None
    for credential_id, account, username in rows:
        print(f"{credential_id}. {account} — {username}")
    choice = input(f"Enter the ID or account name to {action}: ").strip()
    if choice.isdigit():
        for row in rows:
            if row[0] == int(choice):
                return row
    else:
        matches = [row for row in rows if row[1].casefold() == choice.casefold()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            print("That account name appears more than once. Choose its numeric ID.")
            return None
    print("No matching credential found.")
    return None


def retrieve_password(connection, cipher):
    """Select a credential and decrypt its password for display."""
    row = choose_credential(connection, "retrieve")
    if row is None:
        return
    try:
        column = credential_password_column(connection)
        encrypted = connection.execute(
            f"SELECT {column} FROM credentials WHERE id = ?", (row[0],)
        ).fetchone()
        if encrypted is None or not isinstance(encrypted[0], bytes):
            print("Could not read this password. The database may be damaged.")
            return
        password = cipher.decrypt(encrypted[0]).decode("utf-8")
        print(f"Password for {row[1]} ({row[2]}): {password}")
    except (InvalidToken, UnicodeDecodeError, TypeError, IndexError):
        print("Could not decrypt this password. The database may be damaged.")


def delete_credential(connection):
    """Select and remove a credential after asking for confirmation."""
    row = choose_credential(connection, "delete")
    if row is None:
        return
    confirm = input(f"Delete {row[1]} ({row[2]})? Type 'yes' to confirm: ")
    if confirm.strip().casefold() != "yes":
        print("Deletion cancelled.")
        return
    connection.execute("DELETE FROM credentials WHERE id = ?", (row[0],))
    connection.commit()
    print("Credential deleted.")


def generate_password():
    """Generate a strong password containing each character category."""
    try:
        length_text = input("Password length (12–128, default 20): ").strip()
        length = 20 if not length_text else int(length_text)
        if not 12 <= length <= 128:
            print("Choose a length from 12 to 128.")
            return
    except ValueError:
        print("Enter a whole number for the password length.")
        return

    groups = [string.ascii_lowercase, string.ascii_uppercase, string.digits, "!@#$%^&*()-_=+"]
    password_chars = [secrets.choice(group) for group in groups]
    all_chars = "".join(groups)
    password_chars.extend(secrets.choice(all_chars) for _ in range(length - len(password_chars)))
    secrets.SystemRandom().shuffle(password_chars)
    print("Generated password:", "".join(password_chars))


def main():
    """Unlock the vault, then run the interactive menu."""
    connection = connect_database()
    try:
        cipher = unlock(connection)
        if cipher is None:
            print("Too many incorrect attempts. The vault remains locked.")
            return

        actions = {
            "1": lambda: add_credential(connection, cipher),
            "2": lambda: list_accounts(connection),
            "3": lambda: retrieve_password(connection, cipher),
            "4": lambda: delete_credential(connection),
            "5": generate_password,
        }
        while True:
            print("\nSecure Password Manager")
            print("1. Add credential\n2. List accounts\n3. Retrieve password")
            print("4. Delete credential\n5. Generate password\n6. Exit")
            choice = input("Choose an option: ").strip()
            if choice == "6":
                print("Vault locked. Goodbye.")
                break
            action = actions.get(choice)
            if action is None:
                print("Invalid choice. Enter a number from 1 to 6.")
                continue
            try:
                action()
            except Exception as error:
                print(f"Could not complete that action ({type(error).__name__}).")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting and locking the vault.")
    except Exception:
        print("The vault could not be opened safely. Check the database and try again.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
