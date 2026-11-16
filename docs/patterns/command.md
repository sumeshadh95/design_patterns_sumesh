# Command — Actuator Commands

## Problem

Operators start and stop pumps and set light levels from the dashboard.
If the router called the actuator port directly, nothing would record what
was asked, the State check could be skipped, and HTTP code would be mixed
with actuator rules.

## Intent

Command turns a request into an object. The object knows its actuator, its
payload and how to execute itself against a port. Because the request is an
object, it can be checked before it runs, run by an invoker that does not
know what it does, and stored as history in `command_log`.

## Participants

| Role | In this application |
| --- | --- |
| Command | `Command` with `command_type`, `target_state` and `execute(port)` |
| Concrete commands | `StartPumpCommand`, `StopPumpCommand`, `SetLightLevelCommand` |
| Receiver | `ActuatorPort`: the Phase 9 stack ending in `SimulationActuatorAdapter` |
| Invoker | `CommandInvoker.run(command, port)` |
| Client | `CommandService`, called by `POST /api/commands` from the controls UI |

## Registry instead of branching

`COMMANDS` in `domain/commands/invoker.py` maps a type string to a class.
`command_for(command_type, device_id, payload)` looks the class up and builds
the command. An unknown type raises `UnknownCommandError` (400, no row). The
invoker only calls `command.execute(port)`; it never checks
`if command_type == "start_pump"`. A new command is a new class plus one
entry in the registry.

## Execute path

`CommandService.submit` runs every command the same way:

1. Load the device. Missing, or not an actuator: 404.
2. Build the command from the registry. Unknown type: 400, no row.
3. **Guard:** if `command_type` is not in `ActuatorContext.allowed_commands()`
   for the saved state, write `rejected` and stop (409). No `apply`, no state
   write.
4. **Port:** `CommandInvoker.run` calls `execute(port)` on the decorated port
   from `build_actuator_port`.
5. If a decorator raises `PolicyViolationError` (Max run time exceeded),
   write `failed`. `actuator_states` stays unchanged.
6. **State:** after a completed apply, `ActuatorContext.transition` runs only
   when `target_state` differs from the current state (start → `running`,
   stop → `idle`, light → `running`). A running light stays running.
7. Write `success`.

| Status | Meaning | Example | HTTP |
| --- | --- | --- | --- |
| `success` | Applied; state updated if needed | `start_pump` on an idle pump | 200 |
| `failed` | Legal, but the decorated port refused it | `stop_pump` after 30 min running | 200 |
| `rejected` | Illegal in the current state | `stop_pump` on an idle pump | 409 |

## Command object vs calling the port from the router

A router that calls `port.apply(...)` performs the action and forgets it.
The rules (State guard, state update, logging) would have to be repeated in
every route. With command objects, every route goes through one service and
one invoker, the request is stored with its outcome, and adding a command
does not touch the router.

The Phase 9 demo route `POST /api/actuators/{device_id}/apply` called the
port without a command, so Phase 10 removes it.

## Audit

Every attempt is a row in `command_log`, including rejected ones:

| Column | Type |
| --- | --- |
| `id` | UUID primary key |
| `command_type` | VARCHAR |
| `device_id` | UUID, foreign key to `devices` |
| `payload` | JSONB |
| `status` | `success`, `failed` or `rejected` |
| `error_message` | TEXT, nullable |
| `created_at` | timestamptz |

`command_log` records operator intent: what was asked and the outcome.
Phase 9 `actuator_execution_log` records what reached the decorated port and
which policies ran. A rejected command appears only in `command_log`; a failed
command appears in both.

## API

| Route | Purpose |
| --- | --- |
| `POST /api/commands` | Body `{ command_type, device_id, payload? }`; returns the log row |
| `GET /api/commands?limit=50` | History, newest first; `limit` 1–200 |

```json
{
  "id": "<uuid>",
  "command_type": "stop_pump",
  "device_id": "<uuid>",
  "payload": {},
  "status": "rejected",
  "error_message": "stop_pump is not allowed while the actuator is idle.",
  "created_at": "..."
}
```

## Dashboard

The Actuator controls section (`#controls`) has an actuator picker, its state
badge and the buttons `start_pump`, `stop_pump` and `set_light_level`. A
button is disabled when its name is not in `allowed_commands`.
`set_light_level` sends `{ "level": 1 }` unless the Level field is changed.
After a command, the actuators and the command history reload.

## Where in code

| Role | File |
| --- | --- |
| Command base, `UnknownCommandError` | `backend/src/domain/commands/base.py` |
| Pump commands | `backend/src/domain/commands/pump.py` |
| Light command | `backend/src/domain/commands/light.py` |
| Registry and invoker | `backend/src/domain/commands/invoker.py` |
| DTOs | `backend/src/application/commands/dto.py` |
| Service (guard, port, state, log) | `backend/src/application/commands/service.py` |
| `CommandLogRow` | `backend/src/infrastructure/persistence/models.py` |
| Repository | `backend/src/infrastructure/persistence/command_log_repository.py` |
| API routes | `backend/src/interfaces/api/commands.py` |
| Controls UI | `frontend/src/components/commands/CommandPanel.tsx` |
| Tests | `backend/tests/test_commands.py`, `backend/tests/test_commands_api.py` |

## Handoff to Phase 11

Phase 11 (Observer) will publish an event when a command succeeds or fails.
