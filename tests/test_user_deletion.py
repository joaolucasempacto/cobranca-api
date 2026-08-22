from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.models.user import User
from app.routers.users import delete_user, router
from app.services.user_service import UserService


class UserDeletionTests(TestCase):
    def test_model_soft_delete_deactivates_and_marks_deleted(self) -> None:
        user = User(
            email="user@example.com",
            password_hash="hashed",
            is_active=True,
        )

        user.soft_delete()

        self.assertFalse(user.is_active)
        self.assertIsNotNone(user.deleted_at)
        self.assertIsNotNone(user.deleted_at.tzinfo)

    def test_service_soft_deletes_user_and_commits(self) -> None:
        user_id = uuid4()
        user = Mock()
        uow = Mock()
        uow.users.get_by_id.return_value = user

        UserService(uow).delete(user_id)

        user.soft_delete.assert_called_once_with()
        uow.commit.assert_called_once_with()

    def test_router_delegates_delete_to_service(self) -> None:
        user_id = uuid4()
        service = Mock()

        result = delete_user(user_id, service, Mock())

        self.assertIsNone(result)
        service.delete.assert_called_once_with(user_id)

    def test_router_exposes_no_content_delete(self) -> None:
        matching = [
            route
            for route in router.routes
            if route.path == "/users/{user_id}"
            and "DELETE" in (route.methods or set())
        ]

        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].status_code, 204)
