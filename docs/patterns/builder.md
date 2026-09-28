# Builder

## Intent

Builder constructs a valid location configuration step by step. A configuration contains one location and one or more zones, each with moisture thresholds and a schedule.

## Problem

A location configuration has required data and repeated zone data. Creating it through a large constructor or saving a partly filled dictionary could create invalid database records, such as a location with no zones or thresholds in the wrong order.

## Why Builder fits this project

`LocationConfigBuilder` collects the location name and zones incrementally. It validates the complete configuration in `build()` before the repository can save anything to PostgreSQL.

## Fluent Builder workflow

`LocationConfigBuilder` uses fluent method chaining so the application service can assemble a configuration clearly:

```python
config = (
    LocationConfigBuilder()
    .with_location_name("Lab Site A")
    .add_zone("Bench 1", 0.2, 0.45, {"watering": "08:00"})
    .build()
)
```

The fluent syntax is only the interface style. The Builder pattern is provided by assembling a separate `LocationConfig` product and validating the complete configuration in `build()` before persistence.

## Validation

The domain Builder validates that the location name exists, at least one zone exists, thresholds are between `0.0` and `1.0`, and every low threshold is lower than its high threshold. Invalid configurations fail before the repository writes anything to PostgreSQL.

## Comparison with Factory Method and Abstract Factory

Factory Method creates one product type, such as one moisture sensor. Abstract Factory creates a compatible product family, such as a simulation device kit. Builder assembles one valid complex whole in steps: a location plus its zones.

## Why location_id is used

This project uses `location_id` as the relational scope key because locations are the top-level persisted configuration resource. Using the same name in zones, API responses, and future automation features keeps the model consistent. This phase does not use `greenhouse_id`.

## Extension idea

Add an optional location timezone or zone-specific lighting schedule. The Builder can add another step and validate it in `build()` without changing unrelated device-family logic.