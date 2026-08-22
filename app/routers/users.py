from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.dependencies import (
    get_current_user,
    get_user_service,
    require_permission,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("", response_model=list[UserResponse])
def list_users(
    user_service: Annotated[UserService, Depends(get_user_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("users:read")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[UserResponse]:
    users = user_service.list_users(offset=offset, limit=limit)
    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(
    user_id: UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("users:read")),
    ],
) -> UserResponse:
    user = user_service.get_by_id(user_id)
    return UserResponse.model_validate(user)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("users:write")),
    ],
) -> UserResponse:
    user = user_service.create(
        email=payload.email,
        password=payload.password,
        is_active=payload.is_active,
    )
    return UserResponse.model_validate(user)
