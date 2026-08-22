from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies import get_role_service, require_permission
from app.models.user import User
from app.schemas.permission import PermissionResponse
from app.schemas.role import RoleCreate, RoleResponse, RoleUpdate
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


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:read")),
    ],
) -> RoleResponse:
    role = role_service.get_by_id(role_id)
    return RoleResponse.model_validate(role)


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
) -> RoleResponse:
    role = role_service.update(
        role_id=role_id,
        name=payload.name,
        description=payload.description,
    )
    return RoleResponse.model_validate(role)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_role(
    role_id: UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
) -> Response:
    role_service.delete(role_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{role_id}/permissions",
    response_model=list[PermissionResponse],
)
def list_role_permissions(
    role_id: UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:read")),
    ],
) -> list[PermissionResponse]:
    permissions = role_service.list_permissions(role_id)
    return [
        PermissionResponse.model_validate(permission)
        for permission in permissions
    ]


@router.put(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def grant_role_permission(
    role_id: UUID,
    permission_id: UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
) -> Response:
    role_service.grant_permission(role_id, permission_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def revoke_role_permission(
    role_id: UUID,
    permission_id: UUID,
    role_service: Annotated[RoleService, Depends(get_role_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("roles:write")),
    ],
) -> Response:
    role_service.revoke_permission(role_id, permission_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
