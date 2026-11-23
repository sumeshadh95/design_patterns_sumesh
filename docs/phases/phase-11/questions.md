# Phase 11 — Observer questions

**Pattern / focus:** Observer.

**Read first:** [Guide 11](../../materials/guides/11-observer.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example live auction bids) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the event bus, alerts, publishers, and the event feed from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Observer in plain language. What is a **one-to-many** dependency here, and why must the subject notify dependents **without** knowing their concrete classes?

> [!NOTE]
> **_Your Answer_**
>
> Observer lets one object announce that something happened, and every object that cares reacts on its own. The announcer does not call the reactions one by one.
>
> In my app one `reading.created` event can have many reactions: today `MoistureThresholdSubscriber` checks it, and in Phase 12 a WebSocket will forward it too. That is the one-to-many part: one publish, any number of handlers. The subject (`EventBus`) only stores handlers and calls them. If it had to know the concrete classes, every new reaction would mean editing the bus or the publisher, and the reading code would depend on alerts and on the UI.

2. Name the participants (**subject / event bus**, **observer / subscriber**, **concrete observers**, **event**, **publisher**). What does `subscribe` / `unsubscribe` / `publish` (or `notify`) each do? This example’s `EventBus` implements `subscribe` and `publish` only.

> [!NOTE]
> **_Your Answer_**
>
> - **Subject / event bus:** `EventBus`.
> - **Observer / subscriber:** any handler registered on the bus.
> - **Concrete observers:** `MoistureThresholdSubscriber` and `AlertPersistenceSubscriber`.
> - **Events:** `ReadingCreated`, `ThresholdCrossed`, `CommandFailed`, `ActuatorStateChanged`.
> - **Publishers:** `ReadingIngest`, `CommandService` and the transition service (`ActuatorStateService.transition`).
>
> `subscribe(event_type, handler)` adds a handler to the list for that event class. `publish(event)` calls every handler for the event's class, in subscription order. `unsubscribe` would remove a handler. My bus does not need it, because the composition root subscribes everything once at startup.

3. When should you use Observer, and when should you skip it (only one listener forever; or you need a strict multi-step workflow with guaranteed order)?

> [!NOTE]
> **_Your Answer_**
>
> Use it when one action should trigger several independent reactions, and more reactions are likely later. Here, readings and actuator changes feed alerts now and a WebSocket in Phase 12, without changing the publishers.
>
> Skip it when there will only ever be one listener: a direct call is simpler and easier to follow. Also skip it when the steps form a strict workflow that must run in a guaranteed order, with one result and shared error handling. That should be explicit code, like `CommandService.submit` (guard, port, state, log), not a chain of hidden handlers.

## B. This phase of the application

4. Give at least two **domain events** you publish in this lab, including `reading.created` (only when `tracking_enabled` is true), a threshold-crossed event, command-failed, and `ActuatorStateChanged`. The persistence subscriber stores `state.changed` only when that state is `error`. Who publishes `reading.created`, and why do a manual read, the simulation sampler, and MQTT translation share that one ingest publish? Why must a publisher **not** import the alerts repository or the UI?

> [!NOTE]
> **_Your Answer_**
>
> I publish four events:
> - `ReadingCreated` (`reading.created`), only when the device's `tracking_enabled` is true;
> - `ThresholdCrossed` (`threshold.crossed`);
> - `CommandFailed` (`command.failed`);
> - `ActuatorStateChanged` (`state.changed`). The persistence subscriber stores it only for the `error` state.
>
> `ReadingIngest` publishes `reading.created` in `_persist`, right after the reading row is inserted. A manual read (`take_reading`), the simulation sampler (which calls `take_reading`) and a translated MQTT payload (`record`) all go through `_persist`. So there is one publish rule, applied the same way everywhere, and no source can forget it or publish twice.
>
> A publisher must not import the alerts repository or the UI because then it would know its consumers. Every new reaction would change the publisher, its tests would need the alerts table, and the reading path would break if alert storage broke. The publisher should only say what happened.

5. What does `AlertPersistenceSubscriber` (or your equivalent) do when it handles an event? Name the three stored rows: `threshold.crossed` / `warning` / `Moisture below zone low`, `command.failed` / `warning` / the failure message, and `state.changed` / `critical` / `Actuator entered error`. Why do alerts live in the `alerts` table so the event feed still shows them after a **refresh**?

> [!NOTE]
> **_Your Answer_**
>
> It turns the event into one `active` row in `alerts` through `AlertRepository`. It copies `device_id`, `location_id` and `zone_id` from the event and sets the severity, message and event type:
>
> | Event type | Severity | Message |
> | --- | --- | --- |
> | `threshold.crossed` | `warning` | `Moisture below zone low` |
> | `command.failed` | `warning` | the failure message, e.g. `Max run time exceeded` |
> | `state.changed` | `critical` | `Actuator entered error` (only when the state is `error`) |
>
> Alerts live in the table because React state disappears on refresh, and only that browser tab would ever see it. Rows in the database survive refreshes and restarts. Every client sees the same list. The API can filter them by location, zone, status and time, and Phase 13 can resolve them.

6. The dashboard Event feed **polls** `GET /api/alerts` every 5 seconds in this phase. `services/realtime.ts` is only a **stub**. Why is full WebSocket **not** required in this phase? What should Phase 12 plug into so you do **not** re-implement pub/sub inside socket handlers? Phase 12 subscribes a dashboard socket to this same bus, and the example publishes `AlertCreated` after each insert for that socket.

> [!NOTE]
> **_Your Answer_**
>
> This phase is about the Observer pattern inside the backend: publishers, the bus, subscribers and persistence. A 5-second poll is enough to show the alerts. A WebSocket adds a different set of problems (connections, reconnects, fan-out to clients), which belong to Phase 12.
>
> Phase 12 should subscribe a WebSocket broadcaster to the same `EventBus` built in `application/event_bus.py`, for example on an `AlertCreated` event published after each insert, and fill in `subscribeRealtime` in `realtime.ts`. The socket then only forwards events. The publishers and the subscription logic stay the same, so there is no second pub/sub system inside the socket handlers.

7. Describe the must-demo path: a **tracked** low-moisture reading leads to an alert row that appears in the feed after poll. Which objects collaborate (reading pipeline → bus → subscriber → API → UI), and which object must **not** write the alert directly? What is stored, and what is not published, when `tracking_enabled` is false?

> [!NOTE]
> **_Your Answer_**
>
> 1. A tracked moisture sensor is assigned to Bench 1 (low 0.20) and produces 0.10.
> 2. `ReadingIngest` inserts the reading and publishes `ReadingCreated`, with `location_id` and `zone_id` copied from the device.
> 3. `EventBus` calls `MoistureThresholdSubscriber`. It looks up Bench 1's low threshold, sees 0.10 < 0.20, and publishes `ThresholdCrossed`.
> 4. The bus calls `AlertPersistenceSubscriber`, which inserts the `threshold.crossed` warning row.
> 5. `GET /api/alerts?zone_id=<Bench 1>` returns it.
> 6. The `EventFeed` in `#events` shows it on its next 5-second poll.
>
> `ReadingIngest`, the sensors router and the sensor adapters must not write the alert. Only the subscriber does.
>
> With `tracking_enabled` false, the reading row is still stored in `sensor_readings`, but `ReadingCreated` is not published. So no threshold check runs and no alert is created.

## C. Compare, contrast, and scenarios

8. Contrast Observer with **Facade**. Facade simplifies **calling into** a subsystem. Observer **fans out** notifications after something happened. How do both appear in this greenhouse (Phase 7 overview vs this phase)?

> [!NOTE]
> **_Your Answer_**
>
> Facade is a request going in: the caller asks one simple question and waits for one answer. `LocationOverviewFacade.get_overview` hides the repositories and the automation service behind a single call.
>
> Observer is a notification going out after the fact: the publisher says "this happened" and does not wait for an answer or know how many listeners there are.
>
> In the greenhouse the Phase 7 overview pulls a summary when the dashboard asks for it. In Phase 11, ingest and the command and state services push events, and the subscribers react by checking thresholds and storing alerts. The event feed then reads those stored alerts.

9. Contrast Observer with **Command**. Command captures **intent to act**. Observer propagates **outcomes**. How can `execute()` publish an event without the command class knowing who persists alerts?

> [!NOTE]
> **_Your Answer_**
>
> A command object such as `StopPumpCommand` is a request to act, stored with its history in `command_log`. An event such as `CommandFailed` reports what came out of it.
>
> Publishing only needs a reference to the `EventBus` and an event object. The code that runs the command publishes `CommandFailed` or `ActuatorStateChanged`, and the bus delivers it to whatever subscribers were registered in the composition root. Nothing in the command path imports `AlertRepository` or knows that `AlertPersistenceSubscriber` exists.
>
> In my code the publish happens in `CommandService`, right after `CommandInvoker.run` fails or the state is saved. That keeps the command classes focused on calling the port.

10. One subscriber throws during `notify` / `publish` and aborts the loop, so later subscribers never run. Why is that a trap? What should the bus do so a failing alert writer does not block metrics (or later WebSocket) subscribers?

> [!NOTE]
> **_Your Answer_**
>
> It is a trap because the subscribers are supposed to be independent. If the alert writer fails (for example the database is briefly unavailable), every subscriber after it is silently skipped, such as metrics or the WebSocket. The exception can also bubble up into the publisher, so a reading that was already stored looks like a failed request.
>
> The bus should call each handler on its own: catch the exception, log it, and continue with the next handler. My `EventBus.publish` does exactly that with a `try/except` around each handler and `logger.exception`.
