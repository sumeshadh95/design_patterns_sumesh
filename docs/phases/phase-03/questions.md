# Phase 3 — Abstract Factory questions

**Pattern / focus:** Abstract Factory.

**Read first:** [Guide 03](../../materials/guides/03-abstract-factory.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example PDF/HTML export kits) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to device families, provision, and the unified devices API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Abstract Factory in plain language. What goes wrong when related products are chosen independently (`if format` for each piece) instead of as a **family**?

**Your Answer**

Abstract Factory groups related product creation behind a family-level factory so callers get a consistent set of compatible objects. If components are chosen independently using ad-hoc `if` logic, you risk mixing incompatible variants (for example a simulated sensor with an edge-only actuator), causing runtime mismatches and duplicated creation logic spread across the codebase.

2. Name the main participants (**abstract factory**, **concrete factory**, **abstract products**, **concrete products**, **client**). How does choosing a factory at the start **commit** the client to one family?

**Your Answer**

- Abstract factory: the interface declaring creation of a product set (here `DeviceFamilyFactory`).
- Concrete factory: a family implementation such as `SimulationDeviceFactory` or `EdgeHardwareFactory`.
- Abstract products: the domain product types (here `Device`, with roles sensor/actuator).
- Concrete products: family-specific Device instances (simulation vs edge variants).
- Client: the service or caller that asks the factory to produce a kit.

Choosing a concrete factory up-front commits the client to that family's conventions (labels, protocols, defaults). All products returned by that factory share compatible configuration, so the client need not handle cross-family mismatches.

3. When should you use Abstract Factory, and when should you skip it (for example only one product type per request, or mixing siblings is valid)?

**Your Answer**

Use Abstract Factory when multiple related products must be created together and must be consistent as a family (for example sensors + actuators for a deployment). Skip it when requests only need a single independent product, or when mixing variants across families is acceptable — a simpler Factory Method or a small factory function is then sufficient.

## B. This phase of the application

4. In this lab, what is a **device family**, and what does `create_device_set()` (or your equivalent) return? Why must a simulation kit and an edge kit not mix incompatible siblings?

**Your Answer**

A device family represents an environment-level configuration (for example `simulation` vs `edge`) that determines protocols, default configs, and labels. `create_device_set()` returns a list of `Device` domain objects forming a coherent kit (two sensors + two actuators). Mixing simulation and edge siblings would pair incompatible protocols/configs and break runtime assumptions (e.g., a `protocol: sim` sensor paired with a `gpio` actuator), so families must be homogeneous.

5. Phase 2 Factory Method creators still exist. How does Abstract Factory **compose** them rather than replace them? What would you lose if you deleted the sensor creators and inlined all construction inside the family factory?

**Your Answer**

The Abstract Factory composes Phase 2 creators by calling them to produce sensor prototypes and then wrapping/tagging those results for the family (adding `device_family` and family protocol). If the sensor creators were deleted and inline construction used instead, you would lose separation of concerns, testability, and reuse — changes to sensor defaults would need edits in multiple family factories instead of the single creator.

6. Why add a `device_family` column on the existing `devices` table (with a default/backfill such as `"simulation"`) instead of a new table per family? What happens to Phase 2 sensor rows if you forget the backfill?

**Your Answer**

Using a single `devices` table with a `device_family` column preserves a unified schema for all device types and makes queries and joins simpler. It prepares for future phases where new device families share behaviors and relationships. If you forget to backfill or provide a server default, existing Phase 2 rows may have NULL `device_family`, causing filters to miss them and potentially breaking UI assumptions that expect a family value.

7. `POST /api/devices/provision` returns a kit (expected size: two sensors and two actuators). `GET /api/devices` can filter by `family` and `role`. Why must the UI be able to filter by family? Why do `/api/sensors` routes from Phase 2 still need to work?

**Your Answer**

The UI needs family filtering so users can view and manage kits per environment (simulation vs edge) and avoid seeing mixed families. Phase 2 `/api/sensors` routes must still work for backward compatibility and incremental migration: sensor-specific flows and existing dashboards remain functional while device-family features are added.

## C. Compare, contrast, and scenarios

8. Draw the contrast in one paragraph: Factory Method vs Abstract Factory. Use the questions “which **one** product?” versus “which product **line**?” and mention that Abstract Factory often **uses** Factory Method–style methods inside.

**Your Answer**

Factory Method answers “which one product variant do I instantiate?” — it encapsulates the creation of a single product (for example a moisture sensor). Abstract Factory answers “which product line or family should I produce together?” — it creates a set of related products (sensors + actuators) that must be compatible. In practice Abstract Factory often composes Factory Method–style creators internally so family factories can reuse single-product creation logic.

9. A DTO or HTTP handler constructs concrete simulation/edge device types directly, bypassing the family factory. What consistency bug can that reintroduce? How should HTTP stay on the abstract factory / service instead?

**Your Answer**

If handlers build concrete devices directly, they can accidentally mix protocols or omit required family defaults, reintroducing inconsistency and duplicated logic. HTTP handlers should remain thin: accept parameters, call the family service (which uses factories and repositories), and map returned domain devices to DTOs. This keeps creation rules centralized and consistent.

10. Someone proposes a single “god factory” that creates locations, readings, and devices “because we already have a factory.” Why is that a misuse of Abstract Factory?

**Your Answer**

A god factory violates single responsibility and mixes unrelated domains. Abstract Factory is about creating families of closely related products; bundling unrelated concerns (locations, readings, devices) creates brittle, hard-to-test code and hides important separation boundaries. Keep factories focused and compose them at a higher orchestration level if needed.
