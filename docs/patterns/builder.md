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

Validation lives in the domain, in `domain/locations/config_builder.py`. `build()` checks that:

- the location name is not empty;
- there is at least one zone;
- every zone has a name, thresholds between `0.0` and `1.0`, and a low threshold strictly below its high threshold;
- zone names are unique within the location (the same name may exist in another location).

The zone rules are in one function, `validate_zone_fields`, which `build()` and the zone add/edit service both call. Invalid configurations fail before the repository writes anything to PostgreSQL.

## Why device assignment is not a builder method

The builder has no `add_device`. Devices already exist from Phases 2 and 3, and a zone has no id until the configuration is saved, so there is nothing to point `devices.zone_id` at during `build()`.

Assignment is a later update through `ZoneAssignmentService` and `PATCH /api/devices/{id}/zone`. The client sends only `zone_id`; the service copies `location_id` from that zone in the same write, and clears both columns when `zone_id` is null. Moving a device never rebuilds the location.

## Operations on saved locations

These use cases work on saved rows and never call `build()`:

| Use case | Endpoint | Service |
| --- | --- | --- |
| List locations (oldest first) | `GET /api/locations` | `LocationConfigService.list_locations` |
| Delete a location | `DELETE /api/locations/{id}` | `LocationConfigService.delete_location` |
| Add a zone | `POST /api/locations/{id}/zones` | `ZoneService.add_zone` |
| Edit a zone | `PATCH /api/locations/{id}/zones/{zone_id}` | `ZoneService.update_zone` |
| Delete a zone (not the last) | `DELETE /api/locations/{id}/zones/{zone_id}` | `ZoneService.delete_zone` |
| Assign or unassign a device | `PATCH /api/devices/{id}/zone` | `ZoneAssignmentService.assign` |
| List devices in a zone | `GET /api/locations/{id}/zones/{zone_id}/devices` | `ZoneAssignmentService.list_devices` |

Deleting a location removes its zones through `ON DELETE CASCADE`; the device rows stay, and their `zone_id` and `location_id` become null through `ON DELETE SET NULL`. Deleting a zone first clears `zone_id` and `location_id` on its devices in the same transaction, because `ON DELETE SET NULL` on `zone_id` alone would leave `location_id` set. Deleting the last zone of a location returns 400.

## Comparison with Factory Method and Abstract Factory

Factory Method creates one product type, such as one moisture sensor. Abstract Factory creates a compatible product family, such as a simulation device kit. Builder assembles one valid complex whole in steps: a location plus its zones.

## Why location_id is used

This project uses `location_id` as the relational scope key because locations are the top-level persisted configuration resource. Zones, assigned devices, automation rules and the overview all use the same name, which keeps the model consistent. No table or endpoint uses `greenhouse_id`.

## Where in code

| Role | File |
| --- | --- |
| Builder and zone rules | `backend/src/domain/locations/config_builder.py` |
| Entities and errors | `backend/src/domain/locations/entity.py`, `errors.py` |
| Build and save, list, delete | `backend/src/application/locations/config_service.py` |
| Zone add, edit, delete | `backend/src/application/locations/zone_service.py` |
| Device assignment | `backend/src/application/locations/zone_assignment_service.py` |
| Persistence | `backend/src/infrastructure/persistence/location_repository.py` |
| API | `backend/src/interfaces/api/locations.py`, `devices.py` |
| Dashboard | `frontend/src/components/config/`, `frontend/src/components/devices/ZonePicker.tsx` |

## Extension idea

Add an optional location timezone or zone-specific lighting schedule. The Builder can add another step and validate it in `build()` without changing unrelated device-family logic.
