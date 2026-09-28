# Phase 4 — Builder questions

**Pattern / focus:** Builder.

**Read first:** [Guide 04](../../materials/guides/04-builder.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste teaching-example types (for example flight itineraries) as if they were your greenhouse classes.
- When a question asks about *this application*, refer to locations, zones, `location_id`, and the configuration wizard from the lab.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.

## A. Pattern

1. State the intent of Builder in plain language. Why does construction of a complex object need **stepwise assembly** and **validation at the end** (`build()`), instead of a telescoping constructor or a half-filled dict written straight to the database?
Builder creates a complex object step by step and checks that the complete result is valid before it is used. In this project, a location configuration needs a location name plus one or more valid zones. A telescoping constructor would be difficult to read and easy to call incorrectly, while writing a half-filled dictionary directly to PostgreSQL could leave invalid or incomplete data in the database. build() provides one final point where the whole configuration is checked.

2. Name the main participants (**product**, **builder**, **optional director**, **client**). Until `build()` succeeds, is the intermediate object a finished domain product? Why does that distinction matter?
The product is LocationConfig, containing a Location and its zones. The builder is LocationConfigBuilder, which collects the location name and zones. A director is optional; the application service acts as an orchestrator by reading the DTO and calling builder methods in the appropriate order. The client is the location configuration service, called by the API router. Before build() succeeds, the builder only holds intermediate input and is not a finished domain product. This matters because an incomplete configuration must never be persisted or treated as valid.

3. List at least three kinds of invalid configuration a location/zone `build()` should reject in **this** lab (name, zones, moisture thresholds). Why must those rules live in the **domain** builder, not only in the HTTP layer?
The builder should reject an empty location name, a configuration with no zones, an empty zone name, thresholds outside the 0.0–1.0 VWC range, and a zone where the low threshold is equal to or higher than the high threshold. These rules belong in the domain Builder because they are business rules, not HTTP rules. They must still work if the configuration comes from a test, a future CLI, a background process, or another API endpoint.

## B. This phase of the application

4. What aggregate does the builder produce (location plus zones)? Why does this course use **`location_id`** (and never `greenhouse_id`) as the name for that scope?
The Builder produces one location configuration aggregate: a location plus one or more zones that belong to it. The project uses location_id because a location is the top-level persisted scope for zones and later automation behavior. Using one clear name across the database, API, and frontend avoids ambiguity. This phase does not use greenhouse_id.

5. Describe the path from API request to persistence: DTO → builder steps → `build()` → repository. What must **not** be persisted if `build()` raises `ConfigurationError` (or equivalent)?
The path is: the API receives a request DTO, the application service translates each DTO field into Builder calls, build() validates and returns a LocationConfig, and the repository saves the location and zones in one transaction. If build() raises ConfigurationError, neither a location row nor any zone row may be written to the database.

6. Saving a location and its zones must be **one transaction**. What goes wrong if the location row commits and a later zone insert fails? How does that relate to “no half-built aggregates in the database”?
The location and all of its zones must be saved in one transaction. If a location committed first and a later zone insert failed, the database would contain a location without its required configuration. That is a half-built aggregate. A transaction ensures all rows are committed together, or all rows are rolled back together.

7. The configuration wizard UI collects fields in steps. How does that UI map to Builder without turning React (or the HTTP handler) into the place that owns domain validation?
The React wizard collects user input in steps: location name, zone names, and moisture thresholds. It can perform simple inline checks for a better user experience, such as warning when low is not below high. However, the frontend does not own the final business validation. The API sends the request to the application service, and the domain Builder remains the authoritative place that accepts or rejects the complete configuration.

## C. Compare, contrast, and scenarios

8. Contrast Builder with Factory Method and with Abstract Factory. Which pattern answers “which type?”, which answers “which matching kit?”, and which answers “how do we assemble one **valid whole** in steps?”
Factory Method answers “which one product type should be created?”, such as a moisture sensor or light sensor. Abstract Factory answers “which matching kit should be created?”, such as a compatible simulation or edge device family. Builder answers “how do we assemble one valid whole in steps?”, such as a location with one or more valid zones.

9. Fluent method chaining (`builder.add_zone(...).build()`) is a coding style. Why is a fluent interface **not** the same thing as the Builder pattern?
Fluent chaining is only a syntax style in which methods return self, allowing code such as builder.add_zone(...).build(). It is not automatically the Builder pattern. It becomes Builder when the object incrementally assembles a separate product and build() validates and returns a complete valid result. A fluent class without product construction or final validation is simply a fluent interface.

10. A classmate validates thresholds only in FastAPI / Pydantic and leaves `build()` empty. Another mutates builder fields after `build()` while treating the product as immutable. Explain why each is a trap.
Validating only in FastAPI or Pydantic is a trap because another caller could use the domain Builder without passing through HTTP validation. The domain could then create invalid configurations. Leaving build() empty means the Builder does not protect its own product. Mutating Builder fields after build() is also risky because the returned product is meant to be immutable and valid. The Builder should produce a separate immutable LocationConfig; later edits should go through a new build process.