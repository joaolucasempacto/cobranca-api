from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import get_permission_service, require_permission
from app.models.user import User
from app.schemas.permission import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
)
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("", response_model=list[PermissionResponse])
def list_permissions(
    permission_service: Annotated[
        PermissionService,
        Depends(get_permission_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("permissions:read")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[PermissionResponse]:
    permissions = permission_service.list_permissions(
        offset=offset,
        limit=limit,
    )
    return [
        PermissionResponse.model_validate(permission)
        for permission in permissions
    ]


@router.get("/{permission_id}", response_model=PermissionResponse)
def get_permission(
    permission_id: UUID,
    permission_service: Annotated[
        PermissionService,
        Depends(get_permission_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("permissions:read")),
    ],
) -> PermissionResponse:
    permission = permission_service.get_by_id(permission_id)
    return PermissionResponse.model_validate(permission)


@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_permission(
    payload: PermissionCreate,
    permission_service: Annotated[
        PermissionService,
        Depends(get_permission_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("permissions:write")),
    ],
) -> PermissionResponse:
    permission = permission_service.create(
        code=payload.code,
        description=payload.description,
    )
    return PermissionResponse.model_validate(permission)


@router.patch("/{permission_id}", response_model=PermissionResponse)
def update_permission(
    permission_id: UUID,
    payload: PermissionUpdate,
    permission_service: Annotated[
        PermissionService,
        Depends(get_permission_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("permissions:write")),
    ],
) -> PermissionResponse:
    permission = permission_service.update(
        permission_id=permission_id,
        code=payload.code,
        description=payload.description,
    )
    return PermissionResponse.model_validate(permission)
