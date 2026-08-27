from unittest import TestCase
from unittest.mock import Mock

from app.repositories.customer_repository import CustomerRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class UniqueConstraintConsistencyTests(TestCase):
    def _compiled_exists_query(
        self,
        repository: object,
        method_name: str,
        value: str,
    ) -> str:
        session = repository._session
        session.scalar.return_value = None

        getattr(repository, method_name)(value)

        statement = session.scalar.call_args.args[0]
        return str(
            statement.compile(
                compile_kwargs={"literal_binds": True},
            )
        ).lower()

    def test_user_email_existence_matches_database_unique_constraint(
        self,
    ) -> None:
        repository = UserRepository(Mock())

        query = self._compiled_exists_query(
            repository,
            "exists_by_email",
            "person@example.com",
        )

        self.assertIn("users.email", query)
        self.assertNotIn("deleted_at", query)

    def test_role_name_existence_matches_database_unique_constraint(
        self,
    ) -> None:
        repository = RoleRepository(Mock())

        query = self._compiled_exists_query(
            repository,
            "exists_by_name",
            "admin",
        )

        self.assertIn("roles.name", query)
        self.assertNotIn("deleted_at", query)

    def test_permission_code_existence_matches_database_unique_constraint(
        self,
    ) -> None:
        repository = PermissionRepository(Mock())

        query = self._compiled_exists_query(
            repository,
            "exists_by_code",
            "users:read",
        )

        self.assertIn("permissions.code", query)
        self.assertNotIn("deleted_at", query)

    def test_customer_document_existence_matches_database_unique_constraint(
        self,
    ) -> None:
        repository = CustomerRepository(Mock())

        query = self._compiled_exists_query(
            repository,
            "exists_by_document",
            "12345678901",
        )

        self.assertIn("customers.document", query)
        self.assertNotIn("deleted_at", query)
