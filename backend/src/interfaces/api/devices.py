from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.devices.actuator_state_service import (
    ActuatorNotFoundError,
    ActuatorStateService,
)
from application.devices.dto import (
    AssignZoneRequest,
    DeviceDto,
    SamplingUpdateRequest,
    TransitionRequest,
)
from application.devices.family_service import DeviceFamilyService
from application.devices.sampling_service import SamplingService
from application.locations.zone_assignment_service import ZoneAssignmentService
from domain.actuators.state import IllegalTransitionError, UnknownStateError
from domain.devices.sampling import SamplingConfigError
from domain.locations.errors import DeviceNotFoundError, ZoneNotFoundError
from infrastructure.db import get_db
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository

router = APIRouter(prefix="/api/devices", tags=["devices"])


def _describe_one(db: Session, device_repository: DeviceRepository, device):
    return ActuatorStateService(
        device_repository,
        ActuatorStateRepository(db),
    ).describe([device])[0]


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


@router.patch(
    "/{device_id}/zone",
    response_model=DeviceDto,
    responses={404: {"description": "Device or zone not found"}},
)
def assign_device_zone(
    device_id: UUID,
    payload: AssignZoneRequest,
    db: Session = Depends(get_db),
):
    device_repository = DeviceRepository(db)
    service = ZoneAssignmentService(device_repository, LocationRepository(db))

    try:
        device = service.assign(device_id, payload.zone_id)
    except (DeviceNotFoundError, ZoneNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return _describe_one(db, device_repository, device)


@router.patch(
    "/{device_id}/sampling",
    response_model=DeviceDto,
    responses={
        400: {"description": "Interval below 5 seconds"},
        404: {"description": "Device not found"},
    },
)
def update_device_sampling(
    device_id: UUID,
    payload: SamplingUpdateRequest,
    db: Session = Depends(get_db),
):
    device_repository = DeviceRepository(db)

    try:
        device = SamplingService(device_repository).update(
            device_id,
            payload.sampling_interval_seconds,
            payload.tracking_enabled,
        )
    except SamplingConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except DeviceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return _describe_one(db, device_repository, device)


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
