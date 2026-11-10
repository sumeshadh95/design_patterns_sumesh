from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from application.actuators.dto import ApplyCommandRequest, ExecutionDto
from application.actuators.service import (
    ActuatorExecutionService,
    build_actuator_port,
)
from application.devices.actuator_state_service import ActuatorNotFoundError
from domain.actuators.ports import PolicyViolationError
from infrastructure.db import get_db
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)

router = APIRouter(prefix="/api/actuators", tags=["actuators"])


def _service(db: Session) -> ActuatorExecutionService:
    return ActuatorExecutionService(
        DeviceRepository(db),
        ExecutionLogRepository(db),
        build_actuator_port(db),
    )


@router.get("/executions", response_model=list[ExecutionDto])
def list_executions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return _service(db).list_executions(limit)


@router.post(
    "/{device_id}/apply",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Actuator not found"},
        409: {"description": "Blocked by a policy decorator"},
    },
)
def apply_command(
    device_id: UUID,
    payload: ApplyCommandRequest,
    db: Session = Depends(get_db),
):
    # Demo route until Phase 10 (Command). The policy checks live in the
    # decorators, not here.
    try:
        _service(db).apply(device_id, payload.command, payload.payload)
    except ActuatorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PolicyViolationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
