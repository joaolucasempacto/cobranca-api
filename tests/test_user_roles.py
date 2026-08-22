from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import ConflictError, NotFoundError
from app.services.user_service import UserService


class UserRoleServiceTests(TestCase):
    def test_list_roles_validates_user_and_delegates(self) -> None:
        user_id = uuid4()
        uow = Mock()
        uow.users.get_by_id.return_value = Mock()
        expected = [Mock(), Mock()]
        uow.users.list_roles.return_value = expected

        result = UserService(uow).list_roles(user_id)

        self.assertEqual(result, expected)
        uow.users.list_roles.assert_called_once_with(user_id)

    def test_grant_role_persists_and_commits(self) -> None:
        user_id = uuid4()
        role_id = uuid4()
        uow = Mock()
        uow.users.get_by_id.return_value = Mock()
        uow.roles.get_by_id.return_value = Mock()
        uow.users.has_role.return_value = False

        UserService(uow).grant_role(user_id, role_id)

        uow.users.add_role.assert_called_once_with(user_id, role_id)
        uow.commit.assert_called_once_with()

    def test_grant_role_rejects_duplicate_assignment(self) -> None:
        user_id = uuid4()
        role_id = uuid4()
        uow = Mock()
        uow.users.get_by_id.return_value = Mock()
        uow.roles.get_by_id.return_value = Mock()
        uow.users.has_role.return_value = True

        with self.assertRaisesRegex(
            ConflictError,
            "Perfil já atribuído ao usuário",
        ):
            UserService(uow).grant_role(user_id, role_id)

        uow.users.add_role.assert_not_called()
        uow.commit.assert_not_called()

    def test_revoke_role_rejects_missing_assignment(self) -> None:
        user_id = uuid4()
        role_id = uuid4()
        uow = Mock()
        uow.users.get_by_id.return_value = Mock()
        uow.roles.get_by_id.return_value = Mock()
        uow.users.has_role.return_value = False

        with self.assertRaisesRegex(
            NotFoundError,
            "Perfil não atribuído ao usuário",
        ):
            UserService(uow).revoke_role(user_id, role_id)

        uow.users.remove_role.assert_not_called()
        uow.commit.assert_not_called()
