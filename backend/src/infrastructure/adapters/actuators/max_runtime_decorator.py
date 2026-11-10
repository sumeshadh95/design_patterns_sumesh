from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from domain.actuators.ports import (
    ActuatorDecorator,
    ActuatorPort,
    PolicyViolationError,
)
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MaxRunTimeActuatorDecorator(ActuatorDecorator):
    policy_name = "maxRunTime"

    def __init__(
        self,
        inner: ActuatorPort,
        state_repository: ActuatorStateRepository,
        max_run_time: timedelta,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        super().__init__(inner)
        self._states = state_repository
        self._max_run_time = max_run_time
        self._clock = clock

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        # The running time comes from the persisted Phase 8 state:
        # actuator_states.updated_at is when the actuator entered running.
        running_since = self._states.get_running_since(device_id)

        if (
            running_since is not None
            and self._clock() - running_since >= self._max_run_time
        ):
            # Short-circuit: the inner adapter is never called.
            raise PolicyViolationError("Max run time exceeded")

        super().apply(device_id, command, payload)
