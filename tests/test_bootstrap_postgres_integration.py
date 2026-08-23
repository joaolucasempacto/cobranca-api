from unittest import TestCase
from uuid import uuid4

from sqlalchemy import delete, select

from app.core.security import verify_password
from app.database.session import SessionLocal
from app.models.associations import role_permissions, user_roles
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.unit_of_work import UnitOfWork
from app.services.bootstrap_service import (
    ADMIN_PERMISSIONS,
    ADMIN_ROLE_NAME,
    BootstrapService,
)


class BootstrapPostgreSQLIntegrationTests(TestCase):
    def setUp(self) -> None:
        self.session = SessionLocal()
        self.email = f"bootstrap-{uuid4()}@example.com"
        self.password = "integration-bootstrap-secret"
        self.user_id = None
        self.role_id = None
        self.permission_ids: list = []

        self.existing_role_id = self.session.scalar(
            select(Role.id).where(Role.name == ADMIN_ROLE_NAME)
        )
        self.existing_permission_ids = {
            code: self.session.scalar(
                select(Permission.id).where(Permission.code == code)
            )
            for code, _ in ADMIN_PERMISSIONS
        }

    def tearDown(self) -> None:
        self.session.rollback()

        if self.user_id is not None:
            self.session.execute(
                delete(user_roles).where(
                    user_roles.c.user_id == self.user_id
                )
            )
            self.session.execute(
                delete(User).where(User.id == self.user_id)
            )

        if self.role_id is not None and self.existing_role_id is None:
            self.session.execute(
                delete(role_permissions).where(
                    role_permissions.c.role_id == self.role_id
                )
            )
            self.session.execute(
                delete(Role).where(Role.id == self.role_id)
            )

        created_permission_ids = [
            permission_id
            for code, permission_id in zip(
                (code for code, _ in ADMIN_PERMISSIONS),
                self.permission_ids,
                strict=True,
            )
            if self.existing_permission_ids[code] is None
        ]
        if created_permission_ids:
            self.session.execute(
                delete(role_permissions).where(
                    role_permissions.c.permission_id.in_(
                        created_permission_ids
                    )
                )
            )
            self.session.execute(
                delete(Permission).where(
                    Permission.id.in_(created_permission_ids)
                )
            )

        self.session.commit()
        self.session.close()

    def test_bootstrap_creates_and_reuses_complete_admin_rbac(self) -> None:
        uow = UnitOfWork(self.session)
        service = BootstrapService(uow)

        user = service.bootstrap_admin(self.email, self.password)
        self.user_id = user.id

        role = uow.roles.get_by_name(ADMIN_ROLE_NAME)
        self.assertIsNotNone(role)
        assert role is not None
        self.role_id = role.id

        self.assertTrue(user.is_active)
        self.assertTrue(
            verify_password(self.password, user.password_hash)
        )
        self.assertTrue(uow.users.has_role(user.id, role.id))

        permissions = []
        for code, _ in ADMIN_PERMISSIONS:
            permission = uow.permissions.get_by_code(code)
            self.assertIsNotNone(permission)
            assert permission is not None
            permissions.append(permission)
            self.assertTrue(
                uow.roles.has_permission(role.id, permission.id)
            )

        self.permission_ids = [
            permission.id for permission in permissions
        ]

        repeated_user = service.bootstrap_admin(
            self.email,
            self.password,
        )

        self.assertEqual(repeated_user.id, user.id)
        self.assertEqual(
            len(uow.users.list_roles(user.id)),
            1,
        )
        self.assertEqual(
            len(uow.roles.list_permissions(role.id)),
            len(ADMIN_PERMISSIONS),
        )
