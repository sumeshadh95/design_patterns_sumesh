from __future__ import annotations

from domain.devices.entity import Device
from domain.devices.family_factory import get_family_factory
from infrastructure.persistence.device_repository import DeviceRepository


class DeviceFamilyService:
    def __init__(self, repo: DeviceRepository):
        self._repo = repo

    def provision_family(self, family: str) -> list[Device]:
        factory = get_family_factory(family)
        return self._repo.save_devices(factory.create_device_set())

    def list_devices(
        self,
        *,
        family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return self._repo.list_devices(device_family=family, role=role)