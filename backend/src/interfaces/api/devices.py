from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from application.devices.dto import DeviceDto
from application.devices.family_service import DeviceFamilyService
from application.devices.mappers import devices_to_dtos
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("", response_model=list[DeviceDto])
def list_devices(
    family: str | None = Query(default=None),
    role: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    service = DeviceFamilyService(DeviceRepository(db))
    devices = service.list_devices(family=family, role=role)
    return devices_to_dtos(devices)


@router.post(
    "/provision",
    status_code=status.HTTP_201_CREATED,
    response_model=list[DeviceDto],
)
def provision_devices(
    family: str = Query(...),
    db: Session = Depends(get_db),
):
    service = DeviceFamilyService(DeviceRepository(db))

    try:
        devices = service.provision_family(family)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return devices_to_dtos(devices)