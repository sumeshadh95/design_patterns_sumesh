# Phase 10 — Command questions

**Pattern / focus:** Command.

**Read first:** [Guide 10](../../materials/guides/10-command.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example editor undo commands) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to command objects, the invoker, `command_log`, and the controls UI from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Command in plain language. What does it mean to **objectify a request**, and what can you do with that object that you cannot do with a bare `actuator.start()` call (queue, audit, undo, history)?

> [!NOTE]
> **_Your Answer_**
>
> Command turns "please do this" into an object. Instead of calling a method and forgetting about it, the request becomes a value with its own data: which device, which action, which payload. The object also knows how to carry itself out through `execute()`.
>
> Because the request exists as an object, it can be checked before it runs, passed to an invoker that does not know what it does, stored, queued for later, and written to a history table. With undo support it can also be reversed. A bare `actuator.start()` call happens and is gone: there is nothing to store, nothing to inspect afterwards, and no single place to apply rules before it runs.

2. Name the participants (**command**, **receiver**, **invoker**, **client**). Who creates the command, who triggers `execute()`, and who actually changes actuator/hardware state?

> [!NOTE]
> **_Your Answer_**
>
> - **Command:** the abstract `Command` with `execute(port)`, and the concrete `StartPumpCommand`, `StopPumpCommand` and `SetLightLevelCommand`.
> - **Receiver:** the `ActuatorPort`, which is the Phase 9 stack ending in `SimulationActuatorAdapter`. It does the actual work.
> - **Invoker:** `CommandInvoker`, whose `run(command, port)` calls `execute`.
> - **Client:** `CommandService`, called by `POST /api/commands` when the controls UI sends a command.
>
> The client creates the command from the request with `command_for(...)`. The invoker triggers `execute()`. The adapter at the bottom of the port stack performs the actuator action. After a completed apply, the service saves the new lifecycle state through `ActuatorContext.transition` and the state repository.

3. If a command supports undo, when must it capture the data needed to reverse the action? Why is “capture **before** mutate” critical?

> [!NOTE]
> **_Your Answer_**
>
> It must capture the reversal data inside `execute()`, before it changes anything: for example the previous light level or the previous actuator state.
>
> After the change, the old value is gone, because the receiver now holds the new value. A command that tried to read the "previous" value afterwards would read its own result, and undo would restore the wrong value. Undo is optional in this lab and I did not implement it. A `SetLightLevelCommand` with undo would have to store the old level before calling `apply`.

## B. This phase of the application

4. Which command types did you implement (for example `start_pump`, `stop_pump`, `set_light_level`)? Why does the HTTP handler create a command and pass it to an **invoker** (or application service) instead of calling the actuator adapter from the router?

> [!NOTE]
> **_Your Answer_**
>
> I implemented `start_pump` (`StartPumpCommand`, target state `running`), `stop_pump` (`StopPumpCommand`, target `idle`) and `set_light_level` (`SetLightLevelCommand`, target `running`). A registry maps each type string to its class.
>
> The router only deals with HTTP: it passes the request to `CommandService` and turns the result into a status code. The service builds the command and gives it to the invoker. This way every command takes the same path: State guard, decorated port, state update, `command_log`. No route can skip a step. If the router called the adapter itself, each route would have to repeat those rules, and one forgotten rule would let commands bypass State or the decorators. Adding a new command also does not change the router.

5. Walk through the execute path: (1) consult State / `allowed_commands`, (2) if illegal → **rejected**, (3) if legal → decorated `apply`, update `actuator_states`, log **success** or **failed**. Why must a rejected command **not** change actuator state and **not** reach inner `apply`?

> [!NOTE]
> **_Your Answer_**
>
> `CommandService.submit` first loads the device and its saved state into an `ActuatorContext`.
>
> 1. If `command_type` is not in `allowed_commands()`, it writes a `rejected` row and returns 409.
> 2. Otherwise `CommandInvoker.run` calls `execute(port)` on the stack from `build_actuator_port`: logging, then max run-time, then the simulation adapter.
> 3. If max run-time raises `PolicyViolationError`, it writes `failed` and leaves `actuator_states` as it was.
> 4. Otherwise it calls `ActuatorContext.transition(target_state)` when the target differs, saves the state, and writes `success`.
>
> A rejected command is one that State says makes no sense right now, such as `stop_pump` on an idle pump. If it reached `apply`, a real device would receive a command the lifecycle forbids. If it changed `actuator_states`, the saved state would no longer match the device. Rejecting it before both, while still writing the row, keeps the device and the database correct and leaves a record of the attempt.

6. Distinguish **`rejected`** vs **`failed`** vs **`success`** in `command_log`. Give one greenhouse example of each. Why is “illegal in this state” not the same as “policy or adapter error after the command was accepted”?

> [!NOTE]
> **_Your Answer_**
>
> - **`success`:** the command was legal and applied, and the state was updated if needed. Example: `start_pump` on an idle pump; the pump becomes `running`.
> - **`failed`:** the command was legal, but the decorated port refused or could not do it. Example: `stop_pump` on a pump that has been running for more than 30 minutes; max run-time raises "Max run time exceeded".
> - **`rejected`:** the command is not allowed in the current state, so it was never executed. Example: `stop_pump` on an idle pump.
>
> "Illegal in this state" means the request itself is wrong at this moment, and it is decided by State before anything runs. A policy or adapter error means the request was valid and accepted, but something went wrong while carrying it out. They need different reactions: a rejected command needs a different request, while a failed one points to a policy, the device or the environment. A failed command also has an `actuator_execution_log` row, because it reached the port; a rejected one does not.

7. Why is `command_log` a **different** table from Phase 9 `actuator_execution_log`? What concern does each log record (operator intent vs policy/adapter attempt)?

> [!NOTE]
> **_Your Answer_**
>
> `command_log` records operator intent: what was asked (`command_type`, `payload`), for which device, and the outcome (`success`, `failed` or `rejected`). There is one row per request, including requests that never reached the device.
>
> `actuator_execution_log` records what happened at the actuator port: each attempt that reached the decorator stack, whether it succeeded, and which policies ran. A rejected command appears only in `command_log`. A failed command appears in both, with the operator view in one table and the policy view in the other. Keeping them separate keeps each table about one concern, and lets later code use the port without commands while still being logged.

## C. Compare, contrast, and scenarios

8. Contrast Command with **Strategy**. Strategy is an interchangeable **algorithm** (decide / quote). Command is a **side-effectful request** with history. How do they cooperate in this app (Phase 6 recommends; Phase 10 executes)?

> [!NOTE]
> **_Your Answer_**
>
> Strategy swaps how a decision is computed. `ConservativeMoistureStrategy` and `AggressiveMoistureStrategy` read the same zone context and return a recommendation such as "irrigate" or "wait", without changing anything. Command is a request that does change something (a pump starts) and leaves a history row.
>
> They work together: the Phase 6 strategy says a zone needs water, and a `start_pump` command for that zone's pump carries it out through State, the decorators and `command_log`. Strategy answers "what should happen", and Command makes it happen and records it.

9. Contrast Command with **State**. Who **triggers** the action, and who **decides whether it is legal**? Why must commands not bypass state guards?

> [!NOTE]
> **_Your Answer_**
>
> The command, run by the invoker on the operator's request, triggers the action. State decides whether it is legal: `ActuatorContext.allowed_commands()` says which commands the current state allows, and `transition` checks which state changes are allowed.
>
> If commands bypassed the guard, the lifecycle rules from Phase 8 would mean nothing. A pump in `maintenance` could be started, or an idle pump "stopped", and `actuator_states` would drift away from what the device is really doing. Keeping the rules in State and having every command ask State first means the rules live in one place.

10. The controls UI should disable actions that are not in `allowed_commands`. Why must the **backend** still reject illegal commands even if the UI is correct? What happens if a classmate’s command calls the raw adapter and skips State and Decorator?

> [!NOTE]
> **_Your Answer_**
>
> The UI only helps the user. The page can be out of date (another tab or the Devices section changed the state), and anyone can call `POST /api/commands` directly from Scalar or a script. The backend is the only place that sees the real saved state at the moment of the request, so it must check again and write `rejected` when needed.
>
> A command that calls the raw adapter skips everything around it: no State check, so illegal commands reach the device; no max run-time policy, so a pump can run without limit; no `actuator_execution_log` row; and no consistent state update. The audit trail and the safety rules are both lost.
