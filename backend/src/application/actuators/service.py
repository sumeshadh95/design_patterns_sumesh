from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from application.actuators.dto import ExecutionDto
from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.logging_decorator import (
    LoggingActuatorDecorator,
)
from infrastructure.adapters.actuators.max_runtime_decorator import (
    MaxRunTimeActuatorDecorator,
)
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)
from infrastructure.persistence.models import ActuatorExecutionLogRow
from infrastructure.settings import settings


def build_actuator_port(session: Session) -> ActuatorPort:
    # Composition root for the decorator stack. Order, outermost first:
    # LoggingActuatorDecorator -> MaxRunTimeActuatorDecorator
    # -> SimulationActuatorAdapter
    port: ActuatorPort = SimulationActuatorAdapter()
    port = MaxRunTimeActuatorDecorator(
        port,
        ActuatorStateRepository(session),
        timedelta(seconds=settings.actuator_max_run_seconds),
    )

    return LoggingActuatorDecorator(port, ExecutionLogRepository(session))


def execution_to_dto(row: ActuatorExecutionLogRow) -> ExecutionDto:
    return ExecutionDto(
        id=row.id,
        device_id=row.device_id,
        success=row.success,
        policy_applied=list(row.policy_applied),
        message=row.message,
        created_at=row.created_at,
    )


class ActuatorExecutionService:
    def __init__(self, log_repository: ExecutionLogRepository):
        self._log = log_repository

    def list_executions(self, limit: int = 20) -> list[ExecutionDto]:
        return [execution_to_dto(row) for row in self._log.list_recent(limit)]
