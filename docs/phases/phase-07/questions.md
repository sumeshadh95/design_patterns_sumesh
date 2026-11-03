# Phase 7 — Facade questions

**Pattern / focus:** Facade.

**Read first:** [Guide 07](../../materials/guides/07-facade.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a video publish pipeline) as if they were your greenhouse classes.
- When a question asks about _this application_, refer to the location overview, the facade, and the dashboard Overview page from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Facade in plain language. What problem appears when every HTTP handler (or every UI screen) repeats the same multi-step dance across repositories and services?

> [!NOTE]
> **_Your Answer_**
>
> A Facade gives one simple entry point to a group of subsystems. The caller asks for one thing, and the facade calls the right collaborators in the right order.
>
> When every handler or screen repeats the same steps, the orchestration is duplicated. Each copy knows which repositories exist, which order to call them in and how to combine the results. When one step changes, every copy has to be changed, and the copies start to behave differently.
>
> In this application the dashboard should ask for "the overview of this location". It should not need to know that the answer comes from locations, devices, readings, rules and the strategy service.

2. A facade **orchestrates** collaborators. What should it **not** become (a god object that owns all domain logic)? Where should irrigation policy, sensor translation, and persistence stay instead?

> [!NOTE]
> **_Your Answer_**
>
> A facade should not become a god object that contains the business rules, the SQL and the device translation itself.
>
> In this application each responsibility stays where it already was:
>
> - **Irrigation policy** stays in the strategy classes (`ConservativeMoistureStrategy`, `AggressiveMoistureStrategy`) and is reached through `AutomationService.evaluate()`.
> - **Sensor translation** stays in the sensor adapters from Phase 5.
> - **Persistence** stays in the repositories, such as `OverviewRepository` and `AutomationRuleRepository`.
>
> `LocationOverviewFacade` only calls these collaborators and maps their results into `LocationOverviewDto`.

3. When should you use Facade, and when should you skip it (a single repository call is enough; or you actually need to **translate** a mismatched interface)?

> [!NOTE]
> **_Your Answer_**
>
> Use a Facade when a common use case needs several subsystem calls in a stable order, and when callers should depend on one stable entry point while the internals change.
>
> Skip it when:
>
> - one repository call already answers the question, because the facade would only add indirection
> - the real problem is a mismatched interface that must be translated, because that is the job of an Adapter
> - the facade would grow into one class with many unrelated methods, in which case it should be split by use case
>
> The overview is a good fit because it combines five kinds of data for one screen.

## B. This phase of the application

4. What does `GET /api/locations/{location_id}/overview` return? Name the main pieces of the overview DTO: location, assigned device counts, and `zones` (thresholds, assigned devices, and those devices’ latest readings, including `tracking_enabled` and `sampling_interval_seconds`), plus strategy key and last recommendation. Why may those reading rows come from the sampler or MQTT ingest, not only from `POST /read`? Why is overview scoped by `location_id`?

> [!NOTE]
> **_Your Answer_**
>
> The endpoint returns one `LocationOverviewDto`:
>
> - `location`: the id and name of the location.
> - `device_counts`: the number of **assigned** sensors and actuators (devices with this `location_id` and a `zone_id`).
> - `zones`: every zone of the location, including an empty one. Each zone has its id, name and moisture thresholds, its assigned `devices` (id, type, role, display name), and `latest_readings`: the newest reading of each of those devices that has one, with `value`, `unit`, `recorded_at`, and `tracking_enabled` and `sampling_interval_seconds` copied from the device.
> - `strategy_key`: the saved strategy, or `null` when none is saved.
> - `last_recommendation`: the `action` and `reason` from the automation evaluate service when a key is saved, otherwise `null`.
>
> Readings may come from the sampler or MQTT ingest because, since Phase 5, rows arrive without anyone calling `POST /read`. The overview takes the newest row per device by `recorded_at`, whatever its `source`. Filtering to manual reads would hide most of the data.
>
> The overview is scoped by `location_id` because the location is the site the operator manages. Its zones, the device assignments and the saved strategy all belong to it, so one id selects a consistent snapshot. A missing location returns 404.

5. Why does this phase **not** require a new business table? What already exists from Phases 2–6 that the facade only **composes**?

> [!NOTE]
> **_Your Answer_**
>
> The overview is a read model. It shows data that the earlier phases already store, so nothing new has to be persisted.
>
> The facade composes:
>
> - `devices` from Phases 2 and 3
> - `locations` and `zones` from Phase 4
> - `sensor_readings` from Phase 5
> - `automation_rules` and the strategy service from Phase 6
>
> The last recommendation is computed on each request by calling the strategy service, so it does not need a table either. No migration was added in this phase.

6. The overview HTTP handler should call **only** the facade, not reading/strategy/device repositories directly. Why? How does that help tests and later changes to the query shape?

> [!NOTE]
> **_Your Answer_**
>
> The handler's job is HTTP: read the path parameter, call the use case and map errors to status codes. If it also called several repositories, the orchestration would live in the router and could not be reused.
>
> In this application the handler receives `LocationOverviewFacade` through one `Depends` and calls `get_overview(location_id)`. It imports no repository and no `AutomationService`.
>
> This helps in two ways:
>
> - **Tests:** a handler test can replace one facade instead of several repositories, and the facade can be tested with fake collaborators.
> - **Later changes:** the queries can change, for example to a SQL view or a different join, without touching the router, as long as `LocationOverviewDto` stays the same.

7. The location selector may use the existing locations list. The Overview cards come from **one** overview fetch, and Refresh repeats that same fetch. Why must the React page not stitch device, reading, and automation calls together to build the same snapshot? How does a new reading or a saved strategy show up on overview without extra frontend glue?

> [!NOTE]
> **_Your Answer_**
>
> The location dropdown only uses `GET /api/locations` to choose which `location_id` to show. It is not part of the snapshot. Selecting a location makes one `fetchOverview(locationId)` call, and Refresh repeats that same call.
>
> If the React page called the device, reading and automation endpoints and combined them, the orchestration would move into the browser. The page would need to know the call order, handle several different failures, and could show data from different moments. Every other client would have to repeat the same logic.
>
> A new reading or a saved strategy shows up without extra frontend code because the facade reads the database and evaluates the strategy on every GET. The page only requests the overview again.

## C. Compare, contrast, and scenarios

8. Contrast Facade with **Adapter**. One makes an existing interface usable; the other makes a subsystem simpler to call. Which is which, and how do both appear in this greenhouse app (Phase 5 vs Phase 7)?

> [!NOTE]
> **_Your Answer_**
>
> An **Adapter** makes an existing interface usable by translating it into the interface the application expects. A **Facade** makes a subsystem simpler to call by putting one entry point in front of many parts.
>
> In this application:
>
> - **Phase 5 (Adapter):** `SimulationSensorAdapter` and `VendorStubSensorAdapter` translate different driver payloads into the same normalized `Reading` behind `SensorPort`.
> - **Phase 7 (Facade):** `LocationOverviewFacade` combines the location, devices, readings, rules and recommendation into one overview.
>
> The adapter works on one mismatched component. The facade works on many components that already fit. The facade shows readings that the adapters produced, but it does not translate anything.

9. This phase mentions **N+1** queries. What is an N+1 problem in an overview that lists latest readings for many devices, and what can the facade (or its repository) do about it without putting SQL in the router?

> [!NOTE]
> **_Your Answer_**
>
> An N+1 problem happens when one query loads N devices and then one more query runs for each device to load its latest reading. With 50 devices that is 51 queries, and the number grows with the data.
>
> In this application the repositories use a fixed set of queries:
>
> - one query for the location and one for its zones;
> - one query for the devices assigned to that location (`DeviceRepository.list_assigned_in_location`);
> - one `SELECT DISTINCT ON (device_id) ... ORDER BY device_id, recorded_at DESC` query for the newest reading of exactly those device ids (`OverviewRepository.latest_readings_for`);
> - one read of the saved strategy key.
>
> The device counts are computed from the device list that was already loaded. The only per-zone work is inside the automation evaluate service, which looks up moisture once per zone. That is left in the strategy service on purpose instead of re-implementing `decide` in the facade.
>
> The SQL stays in the repositories. The facade calls them, and the router calls only the facade.

10. A classmate hides every error behind a generic “overview failed,” so a missing location, a DB outage, and a strategy error look the same. Why is that a trap for a facade?

> [!NOTE]
> **_Your Answer_**
>
> A facade should hide complexity, not information. If every failure becomes "overview failed", the caller cannot react correctly.
>
> The three cases need different handling:
>
> - a missing location is a client error and should be a 404
> - a database outage is a server problem that operations must see
> - a strategy error points to bad configuration, such as an unknown key
>
> If they look the same, the dashboard cannot show a useful message, the status code is wrong and debugging takes longer.
>
> In this application the facade raises `LocationNotFoundError` only for a missing location, and the handler maps it to 404. Other exceptions are not caught, so they are not disguised as a missing location.
