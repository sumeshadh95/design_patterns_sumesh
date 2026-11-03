# Phase 2 — Factory Method questions

**Pattern / focus:** Factory Method.

**Read first:** [Guide 02](../../materials/guides/02-factory-method.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example courier notifiers) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to sensors, creators, the `devices` table, and the sensors API from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. State the intent of Factory Method in plain language. What problem appears when callers scatter `new` / constructors (or a growing `if type == ...`) across the application?

> [!NOTE]
> ***Your Answer***
>
> Factory Method separates object creation from object usage. Instead of many callers deciding which concrete class to build, callers request an object through a creator abstraction. This avoids scattered constructors and repeated `if type == ...` logic.

2. Name the main participants of Factory Method (**product**, **concrete product**, **creator**, **concrete creator**, **client**). For each, give one sentence: what it is responsible for.

> [!NOTE]
> ***Your Answer***
>
> - **Product:** Common object type the client needs.
> - **Concrete product:** Specific variant of the product.
> - **Creator:** Declares the factory method (creation contract).
> - **Concrete creator:** Implements the factory method to choose concrete product and defaults.
> - **Client:** Uses products through abstractions, not concrete constructors.

3. How do you add a **new product variant** when creators are polymorphic (new class + registry entry) versus when creation lives in one shared `if/elif` function? Why does that difference matter for extension?

> [!NOTE]
> ***Your Answer***
>
> With polymorphic creators, you add a new creator class and register it. With one shared conditional factory, you keep editing one large function. The polymorphic approach scales better and reduces risk of breaking existing branches.

## B. This phase of the application

4. In this lab, what is the **product** and what are the **concrete creators**? Why must the API handler (or sensor service) go through a creator/registry instead of constructing `MoistureSensor` / `LightSensor` itself?

> [!NOTE]
> ***Your Answer***
>
> The product is the domain `Sensor`. Concrete creators are `MoistureSensorCreator` and `LightSensorCreator`. The API/service must go through the creator registry to keep type mapping and defaults centralized.

5. `POST /api/sensors` accepts a short `type` key such as `"moisture"` or `"light"`, while the stored/returned field is `device_type` (for example `moisture_sensor`). Why are those two fields different? Who decides the stored `device_type` and `default_config`?

> [!NOTE]
> ***Your Answer***
>
> `type` is a short client key (`moisture`, `light`) used to select a creator. `device_type` is the normalized stored value (`moisture_sensor`, `light_sensor`). The creator decides both stored type and default configuration.

6. Why is there a single `devices` table with `role="sensor"` instead of a dedicated `sensors` table? What later phase does that choice prepare for?

> [!NOTE]
> ***Your Answer***
>
> This prepares the schema for later phases where non-sensor device roles (such as actuators) share the same table. `role` supports filtering by family without creating disconnected tables too early.

7. What should happen when the client posts an **unknown** `type`? Where should that rejection be decided (registry/service vs router constructing a concrete class anyway)?

> [!NOTE]
> ***Your Answer***
>
> Unknown type should be rejected with HTTP 400. Rejection should be decided in registry/service creation flow (domain/application boundary), and router should translate that into HTTP semantics.

## C. Compare, contrast, and scenarios

8. Contrast Factory Method with a **simple factory** (one function full of `if type == ...`). When is the simple factory “good enough,” and why does this phase still want polymorphic creators?

> [!NOTE]
> ***Your Answer***
>
> A simple factory is often one function with conditionals and is acceptable for very small and stable scopes. Factory Method is better when types are expected to grow and each type has separate creation rules.

9. Contrast Factory Method with **Abstract Factory** (Phase 3). Factory Method answers which question? Abstract Factory answers which different question? Why is Factory Method enough for Phase 2 sensors?

> [!NOTE]
> ***Your Answer***
>
> Factory Method answers: "How do I create one product family variant through a creator contract?"  
> Abstract Factory answers: "How do I create multiple related products together as a consistent family?"
>
> Phase 2 only requires sensor creation variants, so Factory Method is sufficient.

10. A classmate puts SQLAlchemy session commits (or FastAPI request parsing) **inside** a concrete creator. Why is that a trap? Where should persistence and HTTP stay instead?

> [!NOTE]
> ***Your Answer***
>
> Creators should only define domain creation rules. Database commits belong to repositories/infrastructure, and request parsing belongs to API interfaces. Mixing concerns increases coupling and makes testing and evolution harder.
