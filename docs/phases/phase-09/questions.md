# Phase 9 — Decorator questions

**Pattern / focus:** Decorator.

**Read first:** [Guide 09](../../materials/guides/09-decorator.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example HTTP client wrappers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to `ActuatorPort`, policy decorators, and `actuator_execution_log` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Decorator in plain language. Why is stacking wrappers a flexible alternative to a combinatorial explosion of subclasses (`LoggingRetryMaxRuntimeActuator`, …)?

> [!NOTE]
> ***Your Answer***
>
> Decorator adds behaviour to an object by wrapping it in another object that has the same interface. The wrapper does its extra work and passes the call on to the object inside, so the caller still talks to "an actuator port" and does not know a wrapper is there.
>
> With subclasses, every combination of behaviours needs its own class: logging, max run-time, logging plus max run-time, logging plus retry plus max run-time, and so on. The number of classes grows with every new policy, and code is copied between them. With wrappers each policy is written once as one small class, and any combination is built by stacking the wrappers I need.

2. Name the participants (**component**, **concrete component**, **decorator**, **concrete decorators**). What interface does every decorator present to the caller, and why must that match the wrapped component?

> [!NOTE]
> ***Your Answer***
>
> - **Component:** the shared interface, here `ActuatorPort` with `apply(device_id, command, payload)`.
> - **Concrete component:** the real object that does the base work, here `SimulationActuatorAdapter`.
> - **Decorator:** a class that implements the component interface and holds a reference to an inner component, here `ActuatorDecorator`.
> - **Concrete decorators:** the actual policies, here `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator`.
>
> Every decorator presents the same `apply` method as `ActuatorPort`. It must match because a decorator can wrap either the adapter or another decorator, and the caller must be able to use the stack exactly like the plain adapter. If one wrapper changed the signature, it could no longer be stacked or swapped.

3. **Order matters.** Using logging and retry (or logging and max-run-time) as an example, explain how wrapping A around B can change what you observe compared with wrapping B around A.

> [!NOTE]
> ***Your Answer***
>
> Each wrapper only sees what passes through it, so the order changes what is observed.
>
> In my chain logging is outside max run-time: `Logging → MaxRunTime → Simulation`. When max run-time blocks a command, the exception travels back through the logging decorator, so a `success=false` row is still written. If I swapped them (`MaxRunTime → Logging → Simulation`), a blocked call would stop at max run-time before reaching logging, and the blocked attempt would never appear in the log.
>
> With logging and retry it is similar: logging outside retry writes one entry per logical call, while logging inside retry writes one entry per attempt.

## B. This phase of the application

4. What is `ActuatorPort` here, and which **at least two** decorators did you stack around the real adapter (for example logging and max run-time)? Where is the chain wired (composition root / factory), and why not inside the HTTP router?

> [!NOTE]
> ***Your Answer***
>
> `ActuatorPort` is the domain interface for sending a command to an actuator: `apply(device_id, command, payload) -> None`. The innermost implementation is `SimulationActuatorAdapter` from Phase 5.
>
> I stacked two decorators around it: `MaxRunTimeActuatorDecorator` directly around the adapter, and `LoggingActuatorDecorator` as the outermost wrapper.
>
> The chain is wired in one composition function, `build_actuator_port(session)` in `application/actuators/service.py`. The router only asks for the port and calls `apply`. Keeping the wiring out of the router keeps HTTP code free of policy rules, puts the order in one place, and lets Phase 10 reuse the same decorated port without copying any `if` checks.

5. Max run-time can **short-circuit**: the inner adapter is never called. Why must a blocked attempt still produce a row in `actuator_execution_log` with `success=false` and the policy named in `policy_applied`?

> [!NOTE]
> ***Your Answer***
>
> The log should show every attempt, not only the ones that worked. A blocked command is important information: it shows an actuator ran too long and that a command was refused for that reason. If only successful calls were stored, the operator could not see that the policy acted, and the dashboard would hide the problem.
>
> The row has `success=false` so it is clearly a failure, `policy_applied` (`["maxRunTime", "logging"]`) so it is clear which policy chain handled it, and the message "Max run time exceeded" says why. This works because logging is the outermost decorator: it catches the exception, writes the row, and then re-raises it.

6. How does max run-time know the actuator has been running too long (for example `actuator_states.updated_at` from Phase 8)? Why is that data from **State**, not something the decorator should invent as a second lifecycle?

> [!NOTE]
> ***Your Answer***
>
> It asks `ActuatorStateRepository.get_running_since(device_id)`. If the actuator's state in `actuator_states` is `running`, this returns `updated_at`, which is the time of the last transition, so it is when the actuator started running. The decorator compares `now - running_since`with the configured limit (`ACTUATOR_MAX_RUN_SECONDS`, 1800 seconds = 30 minutes). The clock is injected, so tests can use a fixed time.
>
> The lifecycle already exists in Phase 8. The State pattern owns whether an actuator is running and since when, and it is persisted. If the decorator kept its own timer or flags, there would be two lifecycles that could disagree, for example after a restart or a manual transition. The decorator only reads the State data and applies a rule to it.

7. `GET /api/actuators/executions` feeds the dashboard execution log. Why persist attempts in the database instead of only printing to stdout? What should the UI show after a blocked attempt and a refresh?

> [!NOTE]
> ***Your Answer***
>
> Stdout logs disappear when the container restarts, and they are hard to filter, query or show in the UI. Rows in `actuator_execution_log` are permanent, have a fixed shape (`success`, `policy_applied`, `message`, `created_at`), are linked to the device by a foreign key, and can be returned by an API. That is what lets the dashboard show the history.
>
> After a blocked attempt and a click on Refresh, the Execution log section should show a new row at the top with the time, the device, a red "failed" badge, the policies `maxRunTime, logging` and the message "Max run time exceeded".

## C. Compare, contrast, and scenarios

8. Contrast Decorator with **Adapter**. Both wrap. One **keeps** the interface and **adds** behaviour; the other **changes** the interface and **translates**. Which is which in this greenhouse (Phase 9 vs Phase 5)?

> [!NOTE]
> ***Your Answer***
>
> - **Decorator (Phase 9)** keeps the interface and adds behaviour. `LoggingActuatorDecorator` and `MaxRunTimeActuatorDecorator` implement `ActuatorPort` exactly like the adapter they wrap, and add logging and a run-time check around `apply`.
> - **Adapter (Phase 5)** changes the interface and translates. The simulation, vendor stub and MQTT adapters take a source with its own format and make it fit `SensorPort`, for example turning an MQTT payload into a `Reading`.
>
> Both wrap another object, but the Adapter's goal is to make something incompatible fit, while the Decorator's goal is to add a responsibility to something that already fits.

9. Contrast Decorator with **inheritance** of combined policies. How does composition let you add or remove a policy without a new subclass for every combination?

> [!NOTE]
> ***Your Answer***
>
> With inheritance, each combination of policies is a separate subclass, such as `LoggingActuator`, `MaxRunTimeActuator` and `LoggingMaxRunTimeActuator`. Adding one more policy doubles the possible combinations, and removing a policy means changing the class tree and every subclass that used it.
>
> With composition each policy is one decorator class. The composition root decides which decorators to stack and in what order. Adding a policy is a new wrapper class and one line in `build_actuator_port`; removing one is deleting that line. The adapter and the other decorators do not change.

10. A classmate’s decorator changes the method signature “a little” (extra required argument, different return type). Another ignores wrap order and cannot explain whether logging runs once per logical call or per inner attempt. Explain why each is a trap.

> [!NOTE]
> ***Your Answer***
>
> **Changing the signature:** a decorator must be usable anywhere the component is used. If it needs an extra argument or returns a different type, the caller has to know which wrapper it holds, and the decorator can no longer wrap or be wrapped by the others. That breaks the whole point of the pattern. Changing the interface is Adapter territory, not Decorator.
>
> **Ignoring the order:** the order decides what each wrapper sees. If you cannot say whether logging is outside or inside retry, you cannot say whether the log has one entry per logical call or one per attempt, or whether a blocked call is logged at all. The log then means different things depending on how the stack was built, so the order must be chosen on purpose and documented.
