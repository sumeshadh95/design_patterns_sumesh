from __future__ import annotations

from uuid import UUID

from application.devices.dto import DeviceDto
from application.devices.mappers import device_to_dto
from domain.actuators.context import ActuatorContext
from domain.actuators.state import DEFAULT_STATE
from domain.devices.entity import Device
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository


class ActuatorNotFoundError(LookupError):
    pass


class ActuatorStateService:
    def __init__(
        self,
        device_repository: DeviceRepository,
        state_repository: ActuatorStateRepository,
    ):
        self._devices = device_repository
        self._states = state_repository

    def describe(self, devices: list[Device]) -> list[DeviceDto]:
        actuator_ids = [
            device.id
            for device in devices
            if device.role == "actuator" and device.id is not None
        ]
        states = self._states.get_states(actuator_ids)

        return [
            self._to_dto(device, states.get(device.id, DEFAULT_STATE))
            for device in devices
        ]

    def transition(self, device_id: UUID, target: str) -> DeviceDto:
        device = self._devices.get_device(device_id)

        if device is None or device.role != "actuator":
            raise ActuatorNotFoundError("Actuator not found.")

        current = self._states.get_state(device_id) or DEFAULT_STATE
        context = ActuatorContext(device.device_type, current)

        # The domain guard runs first: an illegal or unknown target raises
        # here, so nothing is saved.
        context.transition(target)
        self._states.save_state(device_id, context.state)

        return device_to_dto(
            device,
            state=context.state,
            allowed_commands=context.allowed_commands(),
        )

    @staticmethod
    def _to_dto(device: Device, state: str) -> DeviceDto:
        if device.role != "actuator":
            return device_to_dto(device)

        context = ActuatorContext(device.device_type, state)

        return device_to_dto(
            device,
            state=context.state,
            allowed_commands=context.allowed_commands(),
        )
