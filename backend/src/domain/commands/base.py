from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar
from uuid import UUID

from domain.actuators.ports import ActuatorPort


class UnknownCommandError(ValueError):
    pass


class Command(ABC):
    """One operator request for one actuator, stored as an object."""

    command_type: ClassVar[str]
    # The state the actuator moves to after a completed apply (None = no move).
    target_state: ClassVar[str | None] = None

    def __init__(self, device_id: UUID, payload: dict[str, Any]) -> None:
        self.device_id = device_id
        self.payload = payload

    @abstractmethod
    def execute(self, port: ActuatorPort) -> None:
        raise NotImplementedError
