# Phase 8 — State questions

**Pattern / focus:** State.

**Read first:** [Guide 08](../../materials/guides/08-state.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example support-ticket states) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to actuator lifecycle, persisted state, and `allowed_commands` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of the State pattern in plain language. What problem appears when lifecycle is modelled as boolean flags and scattered `if` guards?
> **Answer:**
> The State pattern lets an object behave differently depending on the stage of its lifecycle. Each stage is its own object that knows what is allowed in that stage and which stages can follow.
>
> With boolean flags the current mode is hidden in a combination of values. Every method needs its own `if` guards, and a new code path can forget one, so illegal moves slip through. Adding a new mode means editing many methods. The UI also has no clean way to ask what is allowed right now.
>
> In this application an actuator has one explicit state, such as `idle` or `running`, and the rules for that state live in one class.

2. Name the participants (**context**, **state interface**, **concrete states**, **client**). How does a successful command lead to a **transition**, and where do **guards** live?
> **Answer:**
> The participants in this application are:
>
> - **Context:** `ActuatorContext`, which holds the current state and delegates to it.
> - **State interface:** `ActuatorState`, with `can_transition_to()` and `allowed_commands()`.
> - **Concrete states:** `OffState`, `IdleState`, `RunningState`, `ErrorState` and `MaintenanceState`.
> - **Client:** `ActuatorStateService`, the devices API and the dashboard.
>
> A transition happens when the client calls `context.transition(target)`. The context asks the current state whether the target is allowed. If it is, the context replaces its current state object with the new one, and the service saves the new state name.
>
> The guards live in the domain. Each concrete state lists its legal targets, and `ActuatorContext.transition` raises `IllegalTransitionError` when the target is not in that list.

3. What is `allowed_commands` (or equivalent) for? Why is exposing “what can I do **now**?” better than letting the UI guess from a raw state string?
> **Answer:**
> `allowed_commands` is the list of commands that are legal for an actuator in its current state. For a pump it is `["start_pump"]` when idle and `["stop_pump"]` when running.
>
> If the UI only received the raw state string, it would need its own copy of the rules to decide which buttons to enable. That copy would drift from the backend whenever a rule changed.
>
> By exposing `allowed_commands`, the backend stays the single source of the rules. The UI only displays what it receives, and Phase 10 can use the same list to accept or reject a command.

## B. This phase of the application

4. Which actuator states did you implement (for example idle, running, error)? Sketch the **legal** transitions (which command or event moves idle → running, running → idle, into error, and out of error).
> **Answer:**
> All five states are implemented: `off`, `idle`, `running`, `error` and `maintenance`.
>
> The legal transitions are:
>
> ```text
> off          -> idle
> idle         -> running, maintenance, error, off
> running      -> idle, error
> error        -> idle, maintenance
> maintenance  -> idle
> ```
>
> - `idle -> running` is starting the actuator (`start_pump` for a pump).
> - `running -> idle` is stopping it (`stop_pump`).
> - `idle -> error` and `running -> error` represent a fault.
> - `error -> idle` is the reset after the fault is cleared. `error -> maintenance` sends the actuator for service.
>
> Everything else is illegal. For example `running -> maintenance` and `running -> off` are rejected, because the actuator must return to `idle` first.

5. Why is actuator state stored in `actuator_states` (or equivalent) rather than only in process memory? What must still be true after you restart the backend?
> **Answer:**
> Process memory is lost when the backend restarts, and it is not shared if more than one backend process runs. A pump that was `running` would appear as `idle` again, and the system would allow it to be started a second time.
>
> The state is stored in the `actuator_states` table, keyed by `device_id`. Only the state name is stored, and it is turned back into a state object when it is loaded.
>
> After a restart every actuator must still be in the state it was left in, with the same `allowed_commands`.

6. An **illegal** transition must raise a domain error and **must not** update the database. Why? Which HTTP status is reasonable for that case (400 or 409), and why should the rule live in the domain rather than in React?
> **Answer:**
> The stored state must always describe a lifecycle position that was legally reached. If an illegal move were saved, the database would contain a state the rules say is impossible, and every later decision would be based on it.
>
> In this application the service calls `context.transition(target)` before `save_state()`. When the guard raises `IllegalTransitionError`, the save is never reached.
>
> The API returns **409 Conflict** for an illegal transition, because the request is well formed but conflicts with the current state of the actuator. An unknown target state returns 400, because that request is simply invalid.
>
> The rule belongs in the domain because React is only one client. The API can also be called from Scalar, tests or another program, and a rule that exists only in the browser can be bypassed.

7. Device JSON gains `state` and `allowed_commands`. How does the dashboard use those fields (badges, disable illegal buttons)? How does this prepare **Phase 10 Command**?
> **Answer:**
> The Devices section shows a coloured badge for the state of each actuator: slate for idle, emerald for running, red for error and amber for maintenance. The badge tooltip and a line on the card list the `allowed_commands`.
>
> The card also has a small control to request another state. If the move is illegal, the card shows the backend's error message, for example "Cannot move actuator from running to maintenance."
>
> This prepares Phase 10 in two ways. The command names (`start_pump`, `stop_pump`, `set_light_level`) are already defined, and the command service can check `allowed_commands` before it executes anything. The controls UI can disable buttons that are not in the list.

## C. Compare, contrast, and scenarios

8. Contrast State with **Strategy**. Both look like “context delegates to an object.” Who typically **changes** the active object, and is the variation a **lifecycle** or a **selectable policy**? Give a greenhouse example of each (this phase vs Phase 6).
> **Answer:**
> Both patterns delegate to an object behind a shared interface, but the reason for the variation is different.
>
> **Strategy** is a selectable policy. The client chooses the active object. In Phase 6 the operator saves `conservative` or `aggressive` for a location, and that choice stays until the operator changes it.
>
> **State** is a lifecycle. The active object changes because of events on the object itself, and only along legal transitions. In this phase a pump moves from `idle` to `running` when it is started and back to `idle` when it is stopped.
>
> A strategy can be swapped for any other strategy at any time. A state can only be followed by the states its transition list allows.

9. Contrast State with a pile of booleans (`is_running`, `is_fault`, `is_maintenance`). Why do illegal combinations of flags appear, and how do explicit state objects (or a transition table) prevent that?
> **Answer:**
> Three independent booleans allow eight combinations, but only a few of them mean something. Nothing stops `is_running` and `is_maintenance` from both being true, because each flag is set separately and each method has to remember to check the others.
>
> With explicit states an actuator is in exactly one state at a time, stored as one value. Impossible combinations cannot be represented.
>
> The transition list of each state then limits how that one value can change. `RunningState` only allows `idle` and `error`, so a running pump cannot jump to `maintenance`.

10. A classmate puts HTTP status mapping or SQLAlchemy commits **inside** a concrete state class. Another state mutates a flag directly and skips `transition` / `set_state`. Explain why each is a trap.
> **Answer:**
> **HTTP or SQL inside a state class** mixes layers. The state classes are domain code and should only describe lifecycle rules. If they import FastAPI or SQLAlchemy, they can no longer be unit tested without a web server or a database, and a change of framework would force changes to the lifecycle rules. In this application the router maps `IllegalTransitionError` to 409, and the repository does the commit.
>
> **Mutating a flag directly** bypasses the guard. `ActuatorContext.transition` is the single place where a move is checked. If a state changed the value itself, an illegal move could happen without any error, and the stored state could become one that the rules say is unreachable.
>
> Both traps break the same promise: every change of state goes through one guarded method, and the domain knows nothing about HTTP or the database.
