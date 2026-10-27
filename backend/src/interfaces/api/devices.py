from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.devices.actuator_state_service import (
    ActuatorNotFoundError,
    ActuatorStateService,
)
from application.devices.dto import DeviceDto, TransitionRequest
from application.devices.family_service import DeviceFamilyService
from domain.actuators.state import IllegalTransitionError, UnknownStateError
from infrastructure.db import get_db
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceDto])
def list_devices(
    family: str | None = Query(default=None),
    role: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    device_repository = DeviceRepository(db)
    state_repository = ActuatorStateRepository(db)

    service = DeviceFamilyService(device_repository, state_repository)
    devices = service.list_devices(family=family, role=role)

    return ActuatorStateService(device_repository, state_repository).describe(
        devices
    )


@router.post(
    "/provision",
    status_code=status.HTTP_201_CREATED,
    response_model=list[DeviceDto],
)
def provision_devices(
    family: str = Query(...),
    db: Session = Depends(get_db),
):
    device_repository = DeviceRepository(db)
    state_repository = ActuatorStateRepository(db)

    service = DeviceFamilyService(device_repository, state_repository)

    try:
        devices = service.provision_family(family)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ActuatorStateService(device_repository, state_repository).describe(
        devices
    )


@router.post(
    "/{device_id}/transition",
    response_model=DeviceDto,
    responses={
        400: {"description": "Unknown target state"},
        404: {"description": "Actuator not found"},
        409: {"description": "Illegal transition"},
    },
)
def transition_device(
    device_id: UUID,
    payload: TransitionRequest,
    db: Session = Depends(get_db),
):
    service = ActuatorStateService(
        DeviceRepository(db),
        ActuatorStateRepository(db),
    )

    try:
        return service.transition(device_id, payload.target)
    except ActuatorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnknownStateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except IllegalTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
