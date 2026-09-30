from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort

logger = logging.getLogger(__name__)


class SimulationActuatorAdapter(ActuatorPort):
    def __init__(self) -> None:
        self.applied_commands: list[dict[str, Any]] = []

    def apply(
        self,
        device_id: UUID,
        command: str,
        payload: dict[str, Any],
    ) -> None:
        record = {
            "device_id": str(device_id),
            "command": command,
            "payload": payload,
        }
        self.applied_commands.append(record)
        logger.info("Simulated actuator command: %s", record)