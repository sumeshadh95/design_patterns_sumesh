from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar
from uuid import UUID


class PolicyViolationError(Exception):
    """A policy decorator refused the command before it reached the actuator."""


class ActuatorPort(ABC):
    @abstractmethod
    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        raise NotImplementedError

    def policies(self) -> list[str]:
        # The innermost adapter applies no policy.
        return []


class ActuatorDecorator(ActuatorPort):
    """Wraps another ActuatorPort and presents the same apply method."""

    policy_name: ClassVar[str]

    def __init__(self, inner: ActuatorPort) -> None:
        self._inner = inner

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        self._inner.apply(device_id, command, payload)

    def policies(self) -> list[str]:
        # Innermost first, so the chain Logging -> MaxRunTime -> Simulation
        # reports ["maxRunTime", "logging"].
        return [*self._inner.policies(), self.policy_name]
