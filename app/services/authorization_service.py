from uuid import UUID

from app.exceptions.base import ForbiddenError
from app.repositories.unit_of_work import UnitOfWork


class AuthorizationService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def require_permission(self, user_id: UUID, permission_code: str) -> None:
        if not self._uow.users.has_permission(user_id, permission_code):
            raise ForbiddenError("Usuário sem permissão para esta ação")
