from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies import get_charge_service, require_permission
from app.models.user import User
from app.schemas.charge import ChargeCreate, ChargeResponse, ChargeUpdate
from app.services.charge_service import ChargeService

router = APIRouter(prefix="/charges", tags=["charges"])


@router.get("", response_model=list[ChargeResponse])
def list_charges(
    charge_service: Annotated[ChargeService, Depends(get_charge_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("charges:read")),
    ],
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ChargeResponse]:
    charges = charge_service.list_charges(offset=offset, limit=limit)
    return [ChargeResponse.model_validate(charge) for charge in charges]


@router.post(
    "",
    response_model=ChargeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_charge(
    payload: ChargeCreate,
    charge_service: Annotated[ChargeService, Depends(get_charge_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("charges:write")),
    ],
) -> ChargeResponse:
    charge = charge_service.create(
        customer_id=payload.customer_id,
        amount=payload.amount,
        due_date=payload.due_date,
        description=payload.description,
    )
    return ChargeResponse.model_validate(charge)


@router.get("/{charge_id}", response_model=ChargeResponse)
def get_charge(
    charge_id: UUID,
    charge_service: Annotated[ChargeService, Depends(get_charge_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("charges:read")),
    ],
) -> ChargeResponse:
    charge = charge_service.get_by_id(charge_id)
    return ChargeResponse.model_validate(charge)


@router.patch("/{charge_id}", response_model=ChargeResponse)
def update_charge(
    charge_id: UUID,
    payload: ChargeUpdate,
    charge_service: Annotated[ChargeService, Depends(get_charge_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("charges:write")),
    ],
) -> ChargeResponse:
    charge = charge_service.update(
        charge_id,
        amount=payload.amount,
        due_date=payload.due_date,
        description=payload.description,
        description_provided="description" in payload.model_fields_set,
    )
    return ChargeResponse.model_validate(charge)


@router.post("/{charge_id}/cancel", response_model=ChargeResponse)
def cancel_charge(
    charge_id: UUID,
    charge_service: Annotated[ChargeService, Depends(get_charge_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("charges:write")),
    ],
) -> ChargeResponse:
    charge = charge_service.cancel(charge_id)
    return ChargeResponse.model_validate(charge)


@router.delete(
    "/{charge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_charge(
    charge_id: UUID,
    charge_service: Annotated[ChargeService, Depends(get_charge_service)],
    _current_user: Annotated[
        User,
        Depends(require_permission("charges:write")),
    ],
) -> Response:
    charge_service.delete(charge_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
