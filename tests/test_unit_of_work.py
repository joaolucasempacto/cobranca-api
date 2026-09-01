from unittest import TestCase
from unittest.mock import Mock, patch

from app.repositories.unit_of_work import UnitOfWork


class UnitOfWorkTests(TestCase):
    @patch("app.repositories.unit_of_work.ChargeRepository")
    @patch("app.repositories.unit_of_work.CustomerRepository")
    @patch("app.repositories.unit_of_work.RevokedTokenRepository")
    @patch("app.repositories.unit_of_work.PermissionRepository")
    @patch("app.repositories.unit_of_work.RoleRepository")
    @patch("app.repositories.unit_of_work.UserRepository")
    def test_initializes_repositories_with_same_session(
        self,
        user_repository: Mock,
        role_repository: Mock,
        permission_repository: Mock,
        revoked_token_repository: Mock,
        customer_repository: Mock,
        charge_repository: Mock,
    ) -> None:
        session = Mock()

        uow = UnitOfWork(session)

        user_repository.assert_called_once_with(session)
        role_repository.assert_called_once_with(session)
        permission_repository.assert_called_once_with(session)
        revoked_token_repository.assert_called_once_with(session)
        customer_repository.assert_called_once_with(session)
        charge_repository.assert_called_once_with(session)
        self.assertIs(uow.charges, charge_repository.return_value)
        self.assertIs(uow.customers, customer_repository.return_value)
        self.assertIs(uow.users, user_repository.return_value)
        self.assertIs(uow.roles, role_repository.return_value)
        self.assertIs(uow.permissions, permission_repository.return_value)
        self.assertIs(uow.revoked_tokens, revoked_token_repository.return_value)

    def test_commit_delegates_to_session(self) -> None:
        session = Mock()

        UnitOfWork(session).commit()

        session.commit.assert_called_once_with()

    def test_rollback_delegates_to_session(self) -> None:
        session = Mock()

        UnitOfWork(session).rollback()

        session.rollback.assert_called_once_with()

    def test_context_manager_returns_itself(self) -> None:
        uow = UnitOfWork(Mock())

        with uow as entered_uow:
            self.assertIs(entered_uow, uow)

    def test_context_manager_rolls_back_on_exception(self) -> None:
        session = Mock()
        uow = UnitOfWork(session)

        with self.assertRaises(RuntimeError):
            with uow:
                raise RuntimeError("failure")

        session.rollback.assert_called_once_with()
