from __future__ import annotations

from domain.devices.entity import Device
from domain.sensors.creators import get_creator
from infrastructure.persistence.device_repository import DeviceRepository


class SensorService:
    def __init__(self, repo: DeviceRepository):
        self._repo = repo

    def create_sensor(
        self,
        sensor_type: str,
        display_name: str | None = None,
    ) -> Device:
        creator = get_creator(sensor_type)
        prototype = creator.create_sensor(display_name=display_name)
        saved = self._repo.save_sensor(prototype)

        device = self._repo.get_device(saved.id)
        if device is None:
            raise LookupError("Sensor was not saved.")

        return device

    def list_sensors(self) -> list[Device]:
        return self._repo.list_devices(role="sensor")
