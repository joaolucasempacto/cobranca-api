from unittest import TestCase
from unittest.mock import Mock
from uuid import uuid4

from app.exceptions.base import ConflictError
from app.routers.roles import router
from app.schemas.role import RoleUpdate
from app.services.role_service import RoleService


class RoleUpdateTests(TestCase):
    def test_update_role_changes_fields_and_commits(self) -> None:
        uow = Mock()
        role = Mock(name="operator")
        uow.roles.get_by_id.return_value = role
        uow.roles.exists_by_name.return_value = False
        role_id = uuid4()

        result = RoleService(uow).update(
            role_id,
            name="manager",
            description="Gestores",
        )

        self.assertIs(result, role)
        role.update_details.assert_called_once_with(
            name="manager",
            description="Gestores",
        )
        uow.commit.assert_called_once_with()

    def test_update_role_rejects_duplicate_name(self) -> None:
        uow = Mock()
        role = Mock(name="operator")
        uow.roles.get_by_id.return_value = role
        uow.roles.exists_by_name.return_value = True

        with self.assertRaisesRegex(ConflictError, "Perfil já cadastrado"):
            RoleService(uow).update(uuid4(), name="admin")

        role.update_details.assert_not_called()
        uow.commit.assert_not_called()

    def test_update_schema_rejects_empty_payload(self) -> None:
        with self.assertRaises(ValueError):
            RoleUpdate()

    def test_router_exposes_role_update(self) -> None:
        routes = {
            (route.path, tuple(sorted(route.methods or set())))
            for route in router.routes
        }
        self.assertIn(("/roles/{role_id}", ("PATCH",)), routes)
