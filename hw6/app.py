"""A small local password manager backed by SQLite and Fernet encryption."""

import base64
import getpass
import os
import secrets
import sqlite3
import string
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


DATABASE_PATH = Path(__file__).with_name("passwords.db")
VERIFICATION_TEXT = b"Secure Password Manager key check"


def open_database():
    """Open the local database and create its tables if needed."""
    # Make newly created database files private on Unix-like systems.
    old_umask = os.umask(0o077)
    try:
        connection = sqlite3.connect(DATABASE_PATH)
    finally:
        os.umask(old_umask)

    connection.execute(
        "CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value BLOB NOT NULL)"
    )
    connection.execute(
        """CREATE TABLE IF NOT EXISTS credentials (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               account TEXT NOT NULL,
               username TEXT NOT NULL,
               encrypted_password BLOB NOT NULL
           )"""
    )
    connection.commit()
    return connection


def derive_key(master_password, salt):
    """Derive a Fernet-compatible key from a master password and random salt."""
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode("utf-8")))


def unlock(connection):
    """Set up the master password on first use or unlock the existing database."""
    row = connection.execute(
        "SELECT value FROM settings WHERE name = ?", ("salt",)
    ).fetchone()

    if row is None:
        print("Welcome! Create a master password for this password manager.")
        while True:
            master = getpass.getpass("New master password: ")
            if not master:
                print("The master password cannot be empty.")
                continue
            if master != getpass.getpass("Confirm master password: "):
                print("Those passwords did not match. Try again.")
                continue
            break

        salt = secrets.token_bytes(16)
        key = derive_key(master, salt)
        fernet = Fernet(key)
        connection.execute(
            "INSERT INTO settings (name, value) VALUES (?, ?)", ("salt", salt)
        )
        connection.execute(
            "INSERT INTO settings (name, value) VALUES (?, ?)",
            ("verifier", fernet.encrypt(VERIFICATION_TEXT)),
        )
        connection.commit()
        return fernet

    salt = row[0]
    verifier_row = connection.execute(
        "SELECT value FROM settings WHERE name = ?", ("verifier",)
    ).fetchone()
    if verifier_row is None:
        raise sqlite3.DatabaseError("The database is missing its password verifier.")

    for attempt in range(3):
        master = getpass.getpass("Master password: ")
        fernet = Fernet(derive_key(master, salt))
        try:
            if fernet.decrypt(verifier_row[0]) == VERIFICATION_TEXT:
                return fernet
        except InvalidToken:
            pass
        remaining = 2 - attempt
        if remaining:
            print(f"Incorrect master password. {remaining} attempt(s) remaining.")

    return None


def prompt_required(label):
    """Read non-empty text, allowing the user to cancel with an empty value."""
    value = input(f"{label} (leave blank to cancel): ").strip()
    return value or None


def add_credential(connection, fernet):
    """Ask for account details and save the encrypted password."""
    account = prompt_required("Account or service")
    if account is None:
        print("Cancelled.")
        return
    username = prompt_required("Username")
    if username is None:
        print("Cancelled.")
        return
    password = getpass.getpass("Password (leave blank to cancel): ")
    if not password:
        print("Cancelled.")
        return

    connection.execute(
        "INSERT INTO credentials (account, username, encrypted_password) VALUES (?, ?, ?)",
        (account, username, fernet.encrypt(password.encode("utf-8"))),
    )
    connection.commit()
    print("Credential saved.")


def list_credentials(connection):
    """Show saved account names and usernames, but never their passwords."""
    rows = connection.execute(
        "SELECT id, account, username FROM credentials ORDER BY account, id"
    ).fetchall()
    if not rows:
        print("No credentials saved yet.")
        return
    print("\nSaved accounts:")
    for credential_id, account, username in rows:
        print(f"  {credential_id}. {account} — {username}")


def choose_credential(connection, action):
    """Return a credential ID selected from the list, or None on invalid input."""
    list_credentials(connection)
    value = input(f"Enter the credential number to {action} (or blank to cancel): ").strip()
    if not value:
        return None
    if not value.isdigit():
        print("Please enter a number from the list.")
        return None
    return int(value)


def retrieve_password(connection, fernet):
    """Decrypt and display the password for a selected saved account."""
    credential_id = choose_credential(connection, "retrieve")
    if credential_id is None:
        print("Cancelled.")
        return
    row = connection.execute(
        "SELECT account, username, encrypted_password FROM credentials WHERE id = ?",
        (credential_id,),
    ).fetchone()
    if row is None:
        print("No credential has that number.")
        return
    try:
        password = fernet.decrypt(row[2]).decode("utf-8")
    except (InvalidToken, UnicodeDecodeError):
        print("That password could not be decrypted. The database may be damaged.")
        return
    print(f"Account: {row[0]}\nUsername: {row[1]}\nPassword: {password}")


def delete_credential(connection):
    """Delete a selected credential after asking for confirmation."""
    credential_id = choose_credential(connection, "delete")
    if credential_id is None:
        print("Cancelled.")
        return
    row = connection.execute(
        "SELECT account, username FROM credentials WHERE id = ?", (credential_id,)
    ).fetchone()
    if row is None:
        print("No credential has that number.")
        return
    if input(f"Delete {row[0]} ({row[1]})? [y/N]: ").strip().lower() != "y":
        print("Cancelled.")
        return
    connection.execute("DELETE FROM credentials WHERE id = ?", (credential_id,))
    connection.commit()
    print("Credential deleted.")


def generate_password():
    """Generate a strong 20-character password using Python's secrets module."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password_chars = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice(string.punctuation),
    ]
    password_chars.extend(secrets.choice(alphabet) for _ in range(16))
    secrets.SystemRandom().shuffle(password_chars)
    print("Generated password: " + "".join(password_chars))


def main():
    """Unlock the database and run the interactive menu."""
    connection = open_database()
    try:
        fernet = unlock(connection)
        if fernet is None:
            print("Unable to unlock the password manager.")
            return

        actions = {
            "1": lambda: add_credential(connection, fernet),
            "2": lambda: list_credentials(connection),
            "3": lambda: retrieve_password(connection, fernet),
            "4": lambda: delete_credential(connection),
            "5": generate_password,
        }
        while True:
            print(
                "\nSecure Password Manager\n"
                "1. Add credentials\n"
                "2. List accounts\n"
                "3. Retrieve a password\n"
                "4. Delete credentials\n"
                "5. Generate a strong password\n"
                "6. Exit"
            )
            choice = input("Choose an option: ").strip()
            if choice == "6":
                print("Goodbye.")
                break
            action = actions.get(choice)
            if action is None:
                print("Please choose a number from 1 to 6.")
                continue
            try:
                action()
            except (EOFError, KeyboardInterrupt):
                print("\nInput cancelled.")
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
    except sqlite3.Error as error:
        print(f"Database error: {error}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
