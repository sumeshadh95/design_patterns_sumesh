from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from application.readings.dto import ReadingDto
from application.readings.service import ReadingIngest
from application.sensors.service import SensorService
from domain.devices.entity import Device
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class SensorCreateRequest(BaseModel):
    type: str
    display_name: str | None = None


class SensorResponse(BaseModel):
    id: UUID
    device_type: str
    display_name: str | None
    default_config: dict[str, Any]
    zone_id: UUID | None
    location_id: UUID | None
    sampling_interval_seconds: int
    tracking_enabled: bool


router = APIRouter(prefix="/api/sensors", tags=["sensors"])


def _to_response(device: Device) -> SensorResponse:
    return SensorResponse(
        id=device.id,
        device_type=device.device_type,
        display_name=device.display_name,
        default_config=device.default_config,
        zone_id=device.zone_id,
        location_id=device.location_id,
        sampling_interval_seconds=device.sampling_interval_seconds,
        tracking_enabled=device.tracking_enabled,
    )


@router.get("", response_model=list[SensorResponse])
def list_sensors(db: Session = Depends(get_db)):
    service = SensorService(DeviceRepository(db))

    return [_to_response(device) for device in service.list_sensors()]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SensorResponse)
def create_sensor(
    payload: SensorCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        service = SensorService(DeviceRepository(db))
        device = service.create_sensor(payload.type, payload.display_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return _to_response(device)


@router.post("/{device_id}/read", response_model=ReadingDto)
def take_sensor_reading(
    device_id: UUID,
    db: Session = Depends(get_db),
):
    ingest = ReadingIngest(
        device_repository=DeviceRepository(db),
        reading_repository=ReadingRepository(db),
    )

    try:
        return ingest.take_reading(device_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("/{device_id}/readings", response_model=list[ReadingDto])
def list_sensor_readings(
    device_id: UUID,
    limit: int = Query(default=1, ge=1, le=100),
    db: Session = Depends(get_db),
):
    ingest = ReadingIngest(
        device_repository=DeviceRepository(db),
        reading_repository=ReadingRepository(db),
    )

    try:
        return ingest.list_readings(device_id=device_id, limit=limit)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
