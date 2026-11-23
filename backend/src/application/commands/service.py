from __future__ import annotations

from application.commands.dto import CommandLogDto, CommandRequest
from application.devices.actuator_state_service import ActuatorNotFoundError
from domain.actuators.context import ActuatorContext
from domain.actuators.ports import ActuatorPort, PolicyViolationError
from domain.actuators.state import DEFAULT_STATE
from domain.commands.base import Command
from domain.commands.invoker import CommandInvoker, command_for
from domain.events.bus import EventBus
from domain.events.events import ActuatorStateChanged, CommandFailed
from infrastructure.persistence.actuator_state_repository import (
    ActuatorStateRepository,
)
from infrastructure.persistence.command_log_repository import (
    CommandLogRepository,
)
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.models import CommandLogRow


def command_log_to_dto(row: CommandLogRow) -> CommandLogDto:
    return CommandLogDto(
        id=row.id,
        command_type=row.command_type,
        device_id=row.device_id,
        payload=dict(row.payload),
        status=row.status,
        error_message=row.error_message,
        created_at=row.created_at,
    )


class CommandService:
    def __init__(
        self,
        device_repository: DeviceRepository,
        state_repository: ActuatorStateRepository,
        log_repository: CommandLogRepository,
        port: ActuatorPort,
        event_bus: EventBus,
        invoker: CommandInvoker | None = None,
    ):
        self._devices = device_repository
        self._states = state_repository
        self._log = log_repository
        self._port = port
        self._bus = event_bus
        self._invoker = invoker or CommandInvoker()

    def submit(self, request: CommandRequest) -> CommandLogDto:
        device = self._devices.get_device(request.device_id)

        if device is None or device.role != "actuator":
            raise ActuatorNotFoundError("Actuator not found.")

        # An unknown type raises UnknownCommandError here, before any row.
        command = command_for(
            request.command_type,
            request.device_id,
            request.payload,
        )
        context = ActuatorContext(
            device.device_type,
            self._states.get_state(request.device_id) or DEFAULT_STATE,
        )

        # 1. Guard: State decides whether the command is legal right now.
        #    A rejected command never reaches apply and never changes state.
        if command.command_type not in context.allowed_commands():
            return self._record(
                command,
                "rejected",
                f"{command.command_type} is not allowed while the actuator "
                f"is {context.state}.",
            )

        # 2. Port: the Phase 9 decorator stack from build_actuator_port.
        try:
            self._invoker.run(command, self._port)
        except PolicyViolationError as exc:
            # State stays as it was; the logging decorator already wrote
            # the actuator_execution_log row.
            row = self._record(command, "failed", str(exc))
            self._bus.publish(
                CommandFailed(
                    device_id=device.id,
                    location_id=device.location_id,
                    zone_id=device.zone_id,
                    command_type=command.command_type,
                    message=str(exc),
                )
            )
            return row

        # 3. State: only after a completed apply, and only on a real change.
        if (
            command.target_state is not None
            and command.target_state != context.state
        ):
            context.transition(command.target_state)
            self._states.save_state(request.device_id, context.state)
            self._bus.publish(
                ActuatorStateChanged(
                    device_id=device.id,
                    location_id=device.location_id,
                    zone_id=device.zone_id,
                    state=context.state,
                )
            )

        # 4. Log
        return self._record(command, "success", None)

    def list_history(self, limit: int = 50) -> list[CommandLogDto]:
        return [command_log_to_dto(row) for row in self._log.list_recent(limit)]

    def _record(
        self,
        command: Command,
        status: str,
        error_message: str | None,
    ) -> CommandLogDto:
        row = self._log.add(
            command_type=command.command_type,
            device_id=command.device_id,
            payload=command.payload,
            status=status,
            error_message=error_message,
        )

        return command_log_to_dto(row)
