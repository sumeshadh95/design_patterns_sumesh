# Phase 5 — Adapter questions

**Pattern / focus:** Adapter.

**Read first:** [Guide 05](../../materials/guides/05-adapter.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example a legacy XML calendar client) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensor ports, adapters, readings, and `sensor_readings` from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Adapter in plain language. What problem appears when business code speaks a vendor or legacy protocol (odd field names, units, XML, status codes) directly?
> **Answer:** The Adapter pattern converts the interface of a class or driver into another interface that clients expect, allowing classes with incompatible interfaces to work together. When business code speaks directly to vendor protocols, vendor-specific field names, units, and nested payloads leak across the application, coupling business logic tightly to external drivers.

2. Name the participants (**target / port**, **adaptee**, **adapter**, **client**). What does the adapter translate, and what must it **not** decide (business policy)?
> **Answer:**
> - **Target / Port:** `SensorPort` and `ActuatorPort` (domain interfaces defining standard operations).
> - **Adaptee:** The vendor payload / driver / simulation logic.
> - **Adapter:** `SimulationSensorAdapter` and `VendorStubSensorAdapter`.
> - **Client:** `ReadingService` / API router.
> The adapter translates raw vendor/driver payloads into normalized `Reading` objects. It must **not** decide business policies such as irrigation thresholds or automation logic.


3. GoF distinguishes an **object adapter** (composition) from a **class adapter** (inheritance). Which does modern code prefer, and why?
> **Answer:** Modern code prefers **object adapters** (composition) because composition allows delegating to adaptees without inheriting internal details or suffering from multiple-inheritance constraints.

## B. This phase of the application

4. What is `SensorPort` in this lab, and what normalized value type (for example `Reading`) do adapters return? Why do application services depend on the port rather than on a simulation driver or vendor SDK?
> **Answer:** `SensorPort` is an abstract interface defining `read(device: Device) -> Reading`. Adapters return a normalized `Reading` dataclass (`device_id`, `value`, `unit`, `source`, `recorded_at`). Application services depend on `SensorPort` so that devices and underlying protocols can change without touching the application use case.

5. You need **at least two** adapters (simulation and a vendor stub) with **different raw shapes** but the same normalized reading. Why is the different raw shape the point of the exercise? How does the `source` field on a reading show which adapter produced it?
> **Answer:** The different raw shape proves that the adapter is actually translating distinct external interfaces into one uniform shape. The `source` field explicitly records `"simulation"` or `"vendor"`, allowing the system and UI to trace provenance.

6. Readings are **appended** to `sensor_readings` (history grows). Why not keep only the latest value in memory or overwrite a single row? Which later phase consumes this history?
> **Answer:** Appending ensures history survives server/browser restarts and provides a historical record. Phase 6 (Strategy) evaluates these persisted readings, and Phase 13 (Charts) plots them.

7. `POST /api/sensors/{id}/read` runs an adapter, persists, and returns a DTO. What HTTP status is appropriate when the device is missing versus when the adapter fails? Why must the router never see vendor-shaped types?
> **Answer:**
> - Missing device: HTTP 404 (Not Found).
> - Adapter or validation failure: HTTP 400 (Bad Request).
> The router must never see vendor-shaped types to keep the API layer completely decoupled from external hardware payloads.

## C. Compare, contrast, and scenarios

8. Contrast Adapter with **Facade**. Adapter changes the **shape** of an existing interface; Facade simplifies **how to use** a subsystem. Give a greenhouse-shaped example of each (Adapter this phase; Facade in Phase 7).
> **Answer:**
> - **Adapter (Phase 5):** Changes the shape of vendor-specific sensor responses into a unified `Reading`.
> - **Facade (Phase 7):** Provides a simplified entry point to run higher-level greenhouse workflows across multiple subsystems.

9. Contrast Adapter with **Decorator**. Both wrap an object. What is different about the interface they present to the client?
> **Answer:** An **Adapter** changes an incompatible interface to match the client's expected target interface, whereas a **Decorator** preserves the exact same interface while adding behavior (such as logging or caching).

10. A classmate puts irrigation policy (“if moisture &lt; 0.3 then water”) inside the vendor adapter. Why is that a trap? Where should that decision live instead (later Strategy), and what should stay in the adapter?
> **Answer:** Placing policy inside an adapter couples business decisions to a specific driver. If the sensor is swapped, the policy is lost or duplicated. Policy belongs in domain strategies (Phase 6); the adapter must strictly handle data acquisition and translation.
