from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from application.actuators.service import build_actuator_port
from application.commands.dto import CommandLogDto, CommandRequest
from application.commands.service import CommandService
from application.devices.actuator_state_service import ActuatorNotFoundError
from application.event_bus import event_bus
from domain.commands.base import UnknownCommandError
from infrastructure.db import get_db
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.command_log_repository import (
    CommandLogRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository

router = APIRouter(prefix="/api/commands", tags=["commands"])


def _service(db: Session) -> CommandService:
    return CommandService(
        DeviceRepository(db),
        ActuatorStateRepository(db),
        CommandLogRepository(db),
        build_actuator_port(db),
        event_bus,
    )


@router.post(
    "",
    response_model=CommandLogDto,
    responses={
        200: {"description": "Command row with status success or failed"},
        400: {"description": "Unknown command type; no row is written"},
        404: {"description": "Device not found or not an actuator"},
        409: {
            "model": CommandLogDto,
            "description": "Rejected: not allowed in the current state",
        },
    },
)
def submit_command(
    payload: CommandRequest,
    db: Session = Depends(get_db),
):
    try:
        row = _service(db).submit(payload)
    except ActuatorNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except UnknownCommandError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if row.status == "rejected":
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=row.model_dump(mode="json"),
        )

    return row


@router.get("", response_model=list[CommandLogDto])
def list_commands(
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return _service(db).list_history(limit)
