from __future__ import annotations

from typing import Any
from uuid import UUID

from domain.actuators.ports import ActuatorPort
from domain.commands.base import Command, UnknownCommandError
from domain.commands.light import SetLightLevelCommand
from domain.commands.pump import StartPumpCommand, StopPumpCommand

# Registry: the type string maps to a class, so nothing branches on
# command_type.
COMMANDS: dict[str, type[Command]] = {
    command.command_type: command
    for command in (StartPumpCommand, StopPumpCommand, SetLightLevelCommand)
}


def command_for(
    command_type: str,
    device_id: UUID,
    payload: dict[str, Any],
) -> Command:
    try:
        command_class = COMMANDS[command_type]
    except KeyError:
        raise UnknownCommandError(
            f"Unknown command type: {command_type}"
        ) from None

    return command_class(device_id, payload)


class CommandInvoker:
    """Runs any command against the port it is given."""

    def run(self, command: Command, port: ActuatorPort) -> None:
        command.execute(port)
