# Decorator — Actuator Policies

## Problem

Every command sent to an actuator needs cross-cutting policies: each attempt
must be recorded, and a pump that has been running too long must not accept
more commands. Later phases will want more policies of the same kind.

Putting these checks in the router mixes HTTP code with policy rules.
Putting them in subclasses (`LoggingActuator`, `MaxRunTimeActuator`,
`LoggingMaxRunTimeActuator`, …) needs a new class for every combination.

## Intent

Decorator attaches extra behaviour to an object by wrapping it in another
object with the same interface. Each wrapper does its own work and then
delegates to the object inside it. The caller cannot tell how many wrappers
are stacked.

## Participants

| Role | In this application |
| --- | --- |
| Component | `ActuatorPort` with `apply(device_id, command, payload)` |
| Concrete component | `SimulationActuatorAdapter` (Phase 5), the innermost port |
| Decorator | `ActuatorDecorator`: implements `ActuatorPort` and holds `inner` |
| Concrete decorators | `LoggingActuatorDecorator`, `MaxRunTimeActuatorDecorator` |
| Client | `ActuatorExecutionService`, which only sees `ActuatorPort` |

Every decorator keeps the exact `apply` signature. That is what lets a
decorator wrap the adapter or another decorator.

## Wrapping

```text
ActuatorExecutionService
  → LoggingActuatorDecorator        (outermost)
    → MaxRunTimeActuatorDecorator
      → SimulationActuatorAdapter   (innermost)
```

The chain is built in one place, `build_actuator_port(session)` in
`application/actuators/service.py`:

```python
port: ActuatorPort = SimulationActuatorAdapter()
port = MaxRunTimeActuatorDecorator(port, ActuatorStateRepository(session), max_run_time)
return LoggingActuatorDecorator(port, ExecutionLogRepository(session))
```

The router asks for the port and calls `apply`. It has no policy `if`.

## Order

Logging is outermost on purpose:

- It sees every logical call exactly once, including calls that an inner
  policy blocks.
- When max run-time refuses a command, the exception passes through the
  logging decorator, which writes `success=false` and re-raises.

If max run-time were outermost, a blocked call would stop before it reached
logging and no row would be written. The order decides what is observed.

A completed attempt stores `policy_applied: ["logging"]` and `message: null`.
A blocked attempt stores `["maxRunTime", "logging"]` and
`Max run time exceeded`.


## Max run-time

`MaxRunTimeActuatorDecorator` reads the Phase 8 state with
`ActuatorStateRepository.get_running_since(device_id)`. For an actuator in
`running`, that is `actuator_states.updated_at`, because every transition
updates it. When `now - running_since` is at least `ACTUATOR_MAX_RUN_SECONDS` (default 1800, 30 minutes), it raises `PolicyViolationError`
("Max run time exceeded") and does **not** call the inner port. The clock is
injected, so tests can use a fixed time.

## Execution log

Every attempt is a row in `actuator_execution_log`, not only a line on
stdout:

| Column | Type |
| --- | --- |
| `id` | UUID primary key |
| `device_id` | UUID, foreign key to `devices` |
| `success` | BOOLEAN |
| `policy_applied` | JSONB list of policy names |
| `message` | TEXT, nullable |
| `created_at` | timestamptz |

## API

| Route | Purpose |
| --- | --- |
| `GET /api/actuators/executions?limit=20` | Newest execution rows first |
| `POST /api/actuators/{device_id}/apply` | Demo route until Phase 10 (Command) |

```json
{
  "id": "<uuid>",
  "device_id": "<uuid>",
  "success": false,
  "policy_applied": ["maxRunTime", "logging"],
  "message": "Max run time exceeded",
  "created_at": "..."
}
```

| Apply case | Status |
| --- | --- |
| Applied | 204, row with `success=true` |
| Blocked by max run-time | 409, row with `success=false` |
| Missing device or a sensor | 404, no row |

## Dashboard

The Execution log section lists the recent rows with time, device, a
success or failed badge, the policies and the message. It has an empty
state and a Refresh button.
It also explains these rules in an instruction line.
## Decorator vs inheritance

With inheritance, every combination of policies is a new subclass, and
removing one policy means changing the class tree. With decorators each
policy is one small class, and the composition root picks which ones to
stack and in what order. Adding a policy is a new wrapper and one line in
`build_actuator_port`, with no change to the adapter or the other
decorators.

## Decorator vs Adapter

The Phase 5 adapters change an interface: they translate a vendor or MQTT
format into `SensorPort`. The decorators keep `ActuatorPort` unchanged and
add behaviour around it.

## Where in code

| Role | File |
| --- | --- |
| Port, base decorator, `PolicyViolationError` | `backend/src/domain/actuators/ports.py` |
| Innermost adapter | `backend/src/infrastructure/adapters/actuators/simulation.py` |
| Logging decorator | `backend/src/infrastructure/adapters/actuators/logging_decorator.py` |
| Max run-time decorator | `backend/src/infrastructure/adapters/actuators/max_runtime_decorator.py` |
| `ActuatorExecutionLogRow` | `backend/src/infrastructure/persistence/models.py` |
| Repository | `backend/src/infrastructure/persistence/execution_log_repository.py` |
| Composition root and service | `backend/src/application/actuators/service.py` |
| API routes | `backend/src/interfaces/api/actuators.py` |
| Dashboard | `frontend/src/features/actuators/ExecutionLog.tsx` |
| Tests | `backend/tests/test_actuator_decorators.py`, `backend/tests/test_actuator_executions_api.py` |

## Handoff to Phase 10

Phase 10 (Command) will send commands through this same decorated port and
add `command_log`.
