from unittest import TestCase

from app.core.security import hash_password, verify_password


class PasswordSecurityTests(TestCase):
    def test_hash_password_does_not_store_plaintext(self) -> None:
        password = "SenhaForte#2026"

        password_hash = hash_password(password)

        self.assertNotEqual(password_hash, password)
        self.assertTrue(password_hash.startswith("scrypt$"))

    def test_hash_password_uses_random_salt(self) -> None:
        password = "SenhaForte#2026"

        first_hash = hash_password(password)
        second_hash = hash_password(password)

        self.assertNotEqual(first_hash, second_hash)

    def test_verify_password_accepts_correct_password(self) -> None:
        password = "SenhaForte#2026"
        password_hash = hash_password(password)

        self.assertTrue(verify_password(password, password_hash))

    def test_verify_password_rejects_wrong_or_malformed_hash(self) -> None:
        password_hash = hash_password("SenhaForte#2026")

        self.assertFalse(verify_password("SenhaErrada", password_hash))
        self.assertFalse(verify_password("SenhaForte#2026", "invalid-hash"))

    def test_verify_password_rejects_invalid_base64_hash(self) -> None:
        malformed_hash = "scrypt$16384$8$1$a$a"

        self.assertFalse(verify_password("SenhaForte#2026", malformed_hash))
