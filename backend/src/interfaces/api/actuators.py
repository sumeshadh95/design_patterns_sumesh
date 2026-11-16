from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from application.actuators.dto import ExecutionDto
from application.actuators.service import ActuatorExecutionService
from infrastructure.db import get_db
from infrastructure.persistence.execution_log_repository import (
    ExecutionLogRepository,
)

router = APIRouter(prefix="/api/actuators", tags=["actuators"])


@router.get("/executions", response_model=list[ExecutionDto])
def list_executions(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = ActuatorExecutionService(ExecutionLogRepository(db))

    return service.list_executions(limit)
