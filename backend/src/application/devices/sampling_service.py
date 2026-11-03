from __future__ import annotations

from uuid import UUID

from domain.devices.entity import Device
from domain.devices.sampling import validate_sampling_interval
from domain.locations.errors import DeviceNotFoundError
from infrastructure.persistence.device_repository import DeviceRepository


class SamplingService:
    def __init__(self, device_repository: DeviceRepository):
        self._devices = device_repository

    def update(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device:
        validate_sampling_interval(sampling_interval_seconds)

        device = self._devices.set_sampling(
            device_id,
            sampling_interval_seconds,
            tracking_enabled,
        )
        if device is None:
            raise DeviceNotFoundError("Device not found.")

        return device
