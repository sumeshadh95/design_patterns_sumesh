from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from application.devices.actuator_state_service import ActuatorStateService
from application.devices.dto import DeviceDto
from application.locations.config_service import LocationConfigService
from application.locations.dto import (
    BuildLocationConfigRequestDto,
    LocationConfigDto,
    LocationDto,
    ZoneDto,
    ZoneUpsertRequestDto,
)
from application.locations.zone_assignment_service import ZoneAssignmentService
from application.locations.zone_service import ZoneService
from domain.locations.errors import (
    ConfigurationError,
    LocationNotFoundError,
    ZoneNotFoundError,
)
from infrastructure.db import get_db
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.location_repository import LocationRepository

router = APIRouter(prefix="/api/locations", tags=["locations"])

NOT_FOUND = {404: {"description": "Location or zone not found"}}
INVALID = {400: {"description": "Invalid zone fields or last zone"}}


def _not_found(exc: LookupError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


def _bad_request(exc: ValueError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("", response_model=list[LocationDto])
def list_locations(db: Session = Depends(get_db)):
    """All saved locations, oldest first."""
    return LocationConfigService(LocationRepository(db)).list_locations()


@router.post(
    "/config",
    response_model=LocationConfigDto,
    status_code=status.HTTP_201_CREATED,
    responses=INVALID,
)
def create_location_config(
    payload: BuildLocationConfigRequestDto,
    db: Session = Depends(get_db),
):
    service = LocationConfigService(LocationRepository(db))

    try:
        return service.build_and_save(payload)
    except ConfigurationError as exc:
        raise _bad_request(exc) from exc


@router.get(
    "/{location_id}/config",
    response_model=LocationConfigDto,
    responses=NOT_FOUND,
)
def get_location_config(
    location_id: UUID,
    db: Session = Depends(get_db),
):
    service = LocationConfigService(LocationRepository(db))
    config = service.get_config(location_id)

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found.",
        )

    return config


@router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_location(
    location_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        LocationConfigService(LocationRepository(db)).delete_location(location_id)
    except LocationNotFoundError as exc:
        raise _not_found(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{location_id}/zones",
    response_model=ZoneDto,
    status_code=status.HTTP_201_CREATED,
    responses={**NOT_FOUND, **INVALID},
)
def add_zone(
    location_id: UUID,
    payload: ZoneUpsertRequestDto,
    db: Session = Depends(get_db),
):
    service = ZoneService(LocationRepository(db), DeviceRepository(db))

    try:
        return service.add_zone(location_id, payload)
    except LocationNotFoundError as exc:
        raise _not_found(exc) from exc
    except ConfigurationError as exc:
        raise _bad_request(exc) from exc


@router.patch(
    "/{location_id}/zones/{zone_id}",
    response_model=ZoneDto,
    responses={**NOT_FOUND, **INVALID},
)
def update_zone(
    location_id: UUID,
    zone_id: UUID,
    payload: ZoneUpsertRequestDto,
    db: Session = Depends(get_db),
):
    service = ZoneService(LocationRepository(db), DeviceRepository(db))

    try:
        return service.update_zone(location_id, zone_id, payload)
    except (LocationNotFoundError, ZoneNotFoundError) as exc:
        raise _not_found(exc) from exc
    except ConfigurationError as exc:
        raise _bad_request(exc) from exc


@router.delete(
    "/{location_id}/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**NOT_FOUND, **INVALID},
)
def delete_zone(
    location_id: UUID,
    zone_id: UUID,
    db: Session = Depends(get_db),
):
    service = ZoneService(LocationRepository(db), DeviceRepository(db))

    try:
        service.delete_zone(location_id, zone_id)
    except (LocationNotFoundError, ZoneNotFoundError) as exc:
        raise _not_found(exc) from exc
    except ConfigurationError as exc:
        raise _bad_request(exc) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{location_id}/zones/{zone_id}/devices",
    response_model=list[DeviceDto],
    responses=NOT_FOUND,
)
def list_zone_devices(
    location_id: UUID,
    zone_id: UUID,
    db: Session = Depends(get_db),
):
    device_repository = DeviceRepository(db)
    service = ZoneAssignmentService(device_repository, LocationRepository(db))

    try:
        devices = service.list_devices(location_id, zone_id)
    except (LocationNotFoundError, ZoneNotFoundError) as exc:
        raise _not_found(exc) from exc

    return ActuatorStateService(
        device_repository,
        ActuatorStateRepository(db),
    ).describe(devices)
