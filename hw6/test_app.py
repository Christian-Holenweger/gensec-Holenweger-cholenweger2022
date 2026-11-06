"""Isolated tests for the Secure Password Manager."""

import contextlib
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app


class PasswordManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Path(self.temp_dir.name) / "test-passwords.db"
        self.connection = sqlite3.connect(self.database)
        self.connection.execute(
            "CREATE TABLE settings (name TEXT PRIMARY KEY, value BLOB NOT NULL)"
        )
        self.connection.execute(
            """CREATE TABLE credentials (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   account TEXT NOT NULL,
                   username TEXT NOT NULL,
                   encrypted_password BLOB NOT NULL
               )"""
        )
        self.connection.commit()

    def tearDown(self):
        self.connection.close()
        self.temp_dir.cleanup()

    def create_vault(self, master="A-valid-master-password-42"):
        with patch.object(app.getpass, "getpass", side_effect=[master, master]):
            return app.unlock(self.connection)

    def test_weak_and_short_master_passwords_are_rejected(self):
        attempts = ["123", "password", "admin123", "short", "A-valid-master-password-42"]
        with patch.object(app.getpass, "getpass", side_effect=attempts + [attempts[-1]]):
            with contextlib.redirect_stdout(io.StringIO()):
                cipher = app.unlock(self.connection)
        self.assertIsNotNone(cipher)

    def test_valid_master_password_is_accepted(self):
        self.assertIsNotNone(self.create_vault())

    def test_wrong_master_password_denies_access_after_three_attempts(self):
        self.create_vault()
        output = io.StringIO()
        with patch.object(app.getpass, "getpass", side_effect=["wrong"] * 3) as prompt:
            with contextlib.redirect_stdout(output):
                result = app.unlock(self.connection)
        self.assertIsNone(result)
        self.assertEqual(prompt.call_count, 3)
        self.assertIn("Incorrect master password.", output.getvalue())

    def test_blank_and_overlong_account_and_username_are_rejected(self):
        self.create_vault()
        inputs = ["", "  ", "a" * 101, "valid account", "", "  ", "u" * 101,
                  "valid-user"]
        with patch("builtins.input", side_effect=inputs), patch.object(
            app.getpass, "getpass", return_value="dummy-password"
        ), contextlib.redirect_stdout(io.StringIO()):
            app.add_credential(self.connection, self.create_vault())
        self.assertEqual(
            self.connection.execute("SELECT account, username FROM credentials").fetchall(),
            [("valid account", "valid-user")],
        )

    def test_sql_injection_inputs_are_treated_as_data(self):
        cipher = self.create_vault()
        injection = "' OR '1'='1"
        with patch("builtins.input", side_effect=[injection, injection]), patch.object(
            app.getpass, "getpass", return_value="dummy-password"
        ), contextlib.redirect_stdout(io.StringIO()):
            app.add_credential(self.connection, cipher)
        rows = self.connection.execute(
            "SELECT account, username FROM credentials"
        ).fetchall()
        self.assertEqual(rows, [(injection, injection)])
        tables = {row[0] for row in self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )}
        self.assertEqual(tables, {"settings", "credentials", "sqlite_sequence"})

    def test_passwords_are_encrypted_at_rest(self):
        cipher = self.create_vault()
        secret = "dummy-secret-credential"
        with patch("builtins.input", side_effect=["example", "dummy-user"]), patch.object(
            app.getpass, "getpass", return_value=secret
        ), contextlib.redirect_stdout(io.StringIO()):
            app.add_credential(self.connection, cipher)
        stored = self.connection.execute(
            "SELECT encrypted_password FROM credentials"
        ).fetchone()[0]
        self.assertNotIn(secret.encode(), stored)
        self.assertEqual(cipher.decrypt(stored).decode(), secret)

    def test_add_list_retrieve_delete_and_generate_password(self):
        cipher = self.create_vault()
        with patch("builtins.input", side_effect=["Example", "sample-user"]), patch.object(
            app.getpass, "getpass", return_value="dummy-secret"
        ), contextlib.redirect_stdout(io.StringIO()):
            app.add_credential(self.connection, cipher)

        listing = io.StringIO()
        with contextlib.redirect_stdout(listing):
            app.list_accounts(self.connection)
        self.assertIn("Example", listing.getvalue())
        self.assertIn("sample-user", listing.getvalue())

        retrieved = io.StringIO()
        with patch("builtins.input", return_value="1"), contextlib.redirect_stdout(retrieved):
            app.retrieve_password(self.connection, cipher)
        self.assertIn("dummy-secret", retrieved.getvalue())

        with patch("builtins.input", side_effect=["1", "yes"]), contextlib.redirect_stdout(
            io.StringIO()
        ):
            app.delete_credential(self.connection)
        self.assertEqual(
            self.connection.execute("SELECT COUNT(*) FROM credentials").fetchone()[0], 0
        )

        generated = io.StringIO()
        with patch("builtins.input", return_value="24"), contextlib.redirect_stdout(generated):
            app.generate_password()
        password = generated.getvalue().split(":", 1)[1].strip()
        self.assertEqual(len(password), 24)
        self.assertTrue(any(char.islower() for char in password))
        self.assertTrue(any(char.isupper() for char in password))
        self.assertTrue(any(char.isdigit() for char in password))


if __name__ == "__main__":
    unittest.main()
