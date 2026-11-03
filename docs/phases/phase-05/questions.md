# Phase 5 — Adapter questions

**Pattern / focus:** Adapter.

**Read first:** [Guide 05](../../materials/guides/05-adapter.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensor ports, adapters, readings, and `sensor_readings` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?

> [!NOTE]
> ***Your Answer***
>
> The Adapter pattern converts the interface of a class or driver into another interface that clients expect, allowing classes with incompatible interfaces to work together. When business code speaks directly to vendor protocols, vendor-specific field names, units, and nested payloads leak across the application, coupling business logic tightly to external drivers.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?

> [!NOTE]
> ***Your Answer***
>
> - **Target / Port:** `SensorPort` and `ActuatorPort` (domain interfaces defining standard operations).
> - **Adaptee:** the raw source: the in-code simulation generator, the vendor stub's nested payload, or an MQTT payload dict.
> - **Adapter:** `SimulationSensorAdapter`, `VendorStubSensorAdapter`, `MqttSensorAdapter` (translates a payload dict) and `SimulationActuatorAdapter`.
> - **Client:** `ReadingIngest`, used by the read API route and by the `SimulationSampler`.
>
> The adapter translates raw payloads into a normalized `Reading`. It must **not** decide business policy such as irrigation thresholds or automation logic.

3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?

> [!NOTE]
> ***Your Answer***
>
> Modern code prefers **object adapters** (composition) because composition allows delegating to adaptees without inheriting internal details or suffering from multiple-inheritance constraints.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?

> [!NOTE]
> ***Your Answer***
>
> `SensorPort` is an abstract interface defining `read(device: Device) -> Reading`. Adapters return a normalized `Reading` dataclass (`device_id`, `value`, `unit`, `source`, `recorded_at`). Application services depend on `SensorPort` so that devices and underlying protocols can change without touching the application use case.

5. You need three translations onto the same normalized reading: a simulation adapter, a vendor stub, and an MQTT translator that accepts a payload dict. Why is the different raw shape the point of the exercise? How does `source` (`simulation`, `vendor`, or `mqtt`) show which adapter produced the reading, and why must the MQTT translator not open a broker in this phase? Phase 12 may deliver that same dict on a device HTTP route or through an optional broker — why must this phase still not open either transport?

> [!NOTE]
> ***Your Answer***
>
> The different raw shape is the point of the exercise. The simulation adapter generates a value in code, the vendor stub reads a nested payload with other field names (`kind`, `measurement.fraction`, `captured_at`), and the MQTT translator receives a flat dict such as `{"value": 0.41, "unit": "vwc"}`. All three return the same `Reading`. If every input already looked like a `Reading`, there would be nothing to adapt.
>
> Each adapter sets `source` itself: `simulation`, `vendor` or `mqtt`. The stored row and the sensor card therefore show where a value came from, while the rest of the application never sees the raw formats.
>
> `MqttSensorAdapter.translate` only turns a dict into a `Reading`. It opens no broker connection, so its tests pass a plain dict and need nothing running. Receiving messages is a different job (connections, reconnecting, authentication) that Phase 12 adds on a device HTTP route or an optional broker. Keeping translation and transport apart means Phase 12 only has to hand the same dict to `translate` and then to `ReadingIngest.record`; the adapter itself does not change.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row, and which later phase consumes this history? Why do a manual read, the simulation sampler, and (later) MQTT share **one** writer of that table? Why does the sampler skip devices with tracking off and MQTT devices, and why do sensor cards poll the latest stored reading until Phase 12?

> [!NOTE]
> ***Your Answer***
>
> Appending keeps history. A value kept only in memory is lost on restart, and an overwritten row cannot show a trend. Phase 6 Strategy reads the newest stored moisture per zone, Phase 7 shows it on the overview, and the optional Phase 13 charts plot the history.
>
> A manual read, the simulation sampler and later MQTT all go through `ReadingIngest`, the only writer of `sensor_readings`. Persisting, mapping to the DTO and (in Phase 11) publishing `reading.created` then happen in one place, so the three sources cannot drift apart.
>
> The sampler loads only sensors with `protocol` `simulation` and `tracking_enabled` true. A device with tracking off was switched off by the operator. An MQTT device sends its own readings on its own clock, so generating values for it in code would create fake data.
>
> Sensor cards poll `GET /api/sensors/{id}/readings?limit=1` every five seconds because sampler rows arrive without anyone clicking "Read now". The poll is temporary: Phase 12 pushes `reading.created` over a WebSocket and replaces it.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?

> [!NOTE]
> ***Your Answer***
>
> - Missing device: HTTP 404 (Not Found).
> - Adapter or validation failure: HTTP 400 (Bad Request).
> The router must never see vendor-shaped types to keep the API layer completely decoupled from external hardware payloads.

## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).

> [!NOTE]
> ***Your Answer***
>
> - **Adapter (Phase 5):** Changes the shape of vendor-specific sensor responses into a unified `Reading`.
> - **Facade (Phase 7):** Provides a simplified entry point to run higher-level greenhouse workflows across multiple subsystems.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?

> [!NOTE]
> ***Your Answer***
>
> An **Adapter** changes an incompatible interface to match the client's expected target interface, whereas a **Decorator** preserves the exact same interface while adding behavior (such as logging or caching).

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?

> [!NOTE]
> ***Your Answer***
>
> Placing policy inside an adapter couples business decisions to a specific driver. If the sensor is swapped, the policy is lost or duplicated. Policy belongs in domain strategies (Phase 6); the adapter must strictly handle data acquisition and translation.
