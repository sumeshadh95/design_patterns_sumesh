from __future__ import annotations

from domain.actuators.state import DEFAULT_STATE
from domain.devices.entity import Device
from domain.devices.family_factory import get_family_factory
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository


class DeviceFamilyService:
    def __init__(
        self,
        repo: DeviceRepository,
        state_repo: ActuatorStateRepository | None = None,
    ):
        self._repo = repo
        self._state_repo = state_repo

    def provision_family(self, family: str) -> list[Device]:
        factory = get_family_factory(family)
        devices = self._repo.save_devices(factory.create_device_set())

        if self._state_repo is not None:
            # Every new actuator starts its lifecycle in the default state.
            self._state_repo.ensure_states(
                [
                    device.id
                    for device in devices
                    if device.role == "actuator" and device.id is not None
                ],
                DEFAULT_STATE,
            )

        return devices

    def list_devices(
        self,
        *,
        family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        return self._repo.list_devices(device_family=family, role=role)
