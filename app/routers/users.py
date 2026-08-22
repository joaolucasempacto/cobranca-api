from typing import Annotated

from fastapi import APIRouter, Depends, status

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
