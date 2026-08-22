from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_role_service, require_permission
from app.models.user import User
from app.schemas.role import RoleCreate, RoleResponse
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:read")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[RoleResponse]:
    roles = role_service.list_roles(offset=offset, limit=limit)
    return [RoleResponse.model_validate(role) for role in roles]


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_role(
    payload: RoleCreate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
) -> RoleResponse:
    role = role_service.create(
        name=payload.name,
        description=payload.description,
    )
    return RoleResponse.model_validate(role)
