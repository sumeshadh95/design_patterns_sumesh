# Phase 2 — Factory Method questions and answers

**Pattern / focus:** Factory Method.

## A. Pattern

### 1. State the intent of Factory Method in plain language.

Factory Method separates object creation from object usage. Instead of many callers deciding which concrete class to build, callers request an object through a creator abstraction. This avoids scattered constructors and repeated `if type == ...` logic.

### 2. Name the main participants and responsibilities.

- **Product:** Common object type the client needs.
- **Concrete product:** Specific variant of the product.
- **Creator:** Declares the factory method (creation contract).
- **Concrete creator:** Implements the factory method to choose concrete product and defaults.
- **Client:** Uses products through abstractions, not concrete constructors.

### 3. How do you add a new product variant with polymorphic creators vs one shared `if/elif`?

With polymorphic creators, you add a new creator class and register it. With one shared conditional factory, you keep editing one large function. The polymorphic approach scales better and reduces risk of breaking existing branches.

## B. This phase of the application

### 4. In this lab, what is the product and what are the concrete creators?

The product is the domain `Sensor`. Concrete creators are `MoistureSensorCreator` and `LightSensorCreator`. The API/service must go through the creator registry to keep type mapping and defaults centralized.

### 5. Why are POST `type` and stored `device_type` different?

`type` is a short client key (`moisture`, `light`) used to select a creator. `device_type` is the normalized stored value (`moisture_sensor`, `light_sensor`). The creator decides both stored type and default configuration.

### 6. Why a single `devices` table with `role="sensor"`?

This prepares the schema for later phases where non-sensor device roles (such as actuators) share the same table. `role` supports filtering by family without creating disconnected tables too early.

### 7. What should happen on unknown `type`, and where should rejection be decided?

Unknown type should be rejected with HTTP 400. Rejection should be decided in registry/service creation flow (domain/application boundary), and router should translate that into HTTP semantics.

## C. Compare, contrast, and scenarios

### 8. Factory Method vs simple factory.

A simple factory is often one function with conditionals and is acceptable for very small and stable scopes. Factory Method is better when types are expected to grow and each type has separate creation rules.

### 9. Factory Method vs Abstract Factory (Phase 3).

Factory Method answers: "How do I create one product family variant through a creator contract?"  
Abstract Factory answers: "How do I create multiple related products together as a consistent family?"

Phase 2 only requires sensor creation variants, so Factory Method is sufficient.

### 10. Why is putting DB commit or HTTP parsing inside creators a trap?

Creators should only define domain creation rules. Database commits belong to repositories/infrastructure, and request parsing belongs to API interfaces. Mixing concerns increases coupling and makes testing and evolution harder.
