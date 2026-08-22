from unittest import TestCase
from uuid import uuid4

from sqlalchemy import delete

from app.database.session import SessionLocal
from app.models.user import User
from app.repositories.user_repository import UserRepository


class PostgreSQLIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        self.email = f"integration-{uuid4()}@example.com"

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.execute(
            delete(User).where(User.email == self.email)
        )
        self.session.commit()
        self.session.close()

    def test_user_repository_roundtrip_and_soft_delete(self) -> None:
        repository = UserRepository(self.session)
        user = User(
            email=self.email,
            password_hash="integration-test-hash",
        )

        added_user = repository.add(user)
        self.session.commit()

        self.assertIsNotNone(added_user.id)

        stored_user = repository.get_by_email(self.email)
        self.assertIsNotNone(stored_user)
        assert stored_user is not None
        self.assertEqual(stored_user.id, added_user.id)

        stored_user.soft_delete()
        self.session.commit()

        self.assertIsNone(repository.get_by_email(self.email))
