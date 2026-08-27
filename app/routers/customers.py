from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies import get_customer_service, require_permission
from app.models.user import User
from app.schemas.customer import (
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    customer_service: Annotated[
        CustomerService,
        Depends(get_customer_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("customers:read")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[CustomerResponse]:
    customers = customer_service.list_customers(offset=offset, limit=limit)
    return [
        CustomerResponse.model_validate(customer) for customer in customers
    ]


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    payload: CustomerCreate,
    customer_service: Annotated[
        CustomerService,
        Depends(get_customer_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("customers:write")),
    ],
) -> CustomerResponse:
    customer = customer_service.create(
        name=payload.name,
        document=payload.document,
        email=str(payload.email) if payload.email is not None else None,
        phone=payload.phone,
        address=payload.address,
    )
    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    customer_service: Annotated[
        CustomerService,
        Depends(get_customer_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("customers:read")),
    ],
) -> CustomerResponse:
    customer = customer_service.get_by_id(customer_id)
    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    customer_service: Annotated[
        CustomerService,
        Depends(get_customer_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("customers:write")),
    ],
) -> CustomerResponse:
    customer = customer_service.update(
        customer_id,
        name=payload.name,
        document=payload.document,
        email=str(payload.email) if payload.email is not None else None,
        email_provided="email" in payload.model_fields_set,
        phone=payload.phone,
        phone_provided="phone" in payload.model_fields_set,
        address=payload.address,
        address_provided="address" in payload.model_fields_set,
    )
    return CustomerResponse.model_validate(customer)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_customer(
    customer_id: UUID,
    customer_service: Annotated[
        CustomerService,
        Depends(get_customer_service),
    ],
    _current_user: Annotated[
        User,
        Depends(require_permission("customers:write")),
    ],
) -> Response:
    customer_service.delete(customer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
