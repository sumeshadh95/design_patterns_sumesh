from __future__ import annotations

from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorDecorator, ActuatorPort
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)


class LoggingActuatorDecorator(ActuatorDecorator):
    policy_name = "logging"

    def __init__(
        self,
        inner: ActuatorPort,
        log_repository: ExecutionLogRepository,
    ) -> None:
        super().__init__(inner)
        self._log = log_repository

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        # Outermost wrapper: one row per apply, whether it succeeds or not.
        try:
            super().apply(device_id, command, payload)
        except Exception as exc:
            self._log.add(
                device_id,
                success=False,
                policy_applied=self.policies(),
                message=str(exc),
            )
            raise

        self._log.add(
            device_id,
            success=True,
            policy_applied=[self.policy_name],
            message=None,
        )
