from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from application.readings.dto import ReadingDto
from application.readings.service import ReadingService
from application.sensors.service import SensorService
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


router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.get("", response_model=list[SensorResponse])
def list_sensors(db: Session = Depends(get_db)):
    service = SensorService(DeviceRepository(db))

    return [
        SensorResponse(
            id=sensor.id,
            device_type=sensor.device_type,
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        for sensor in service.list_sensors()
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SensorResponse)
def create_sensor(
    payload: SensorCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        service = SensorService(DeviceRepository(db))
        sensor = service.create_sensor(payload.type, payload.display_name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SensorResponse(
        id=sensor.id,
        device_type=sensor.device_type,
        display_name=sensor.display_name,
        default_config=sensor.default_config,
    )


@router.post("/{device_id}/read", response_model=ReadingDto)
def take_sensor_reading(
    device_id: UUID,
    db: Session = Depends(get_db),
):
    service = ReadingService(
        device_repository=DeviceRepository(db),
        reading_repository=ReadingRepository(db),
    )

    try:
        return service.take_reading(device_id)
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
    service = ReadingService(
        device_repository=DeviceRepository(db),
        reading_repository=ReadingRepository(db),
    )

    try:
        return service.list_readings(device_id=device_id, limit=limit)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc