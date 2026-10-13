# Facade — Location Overview

## Problem

The dashboard overview needs data from several subsystems: the location,
the devices, the latest sensor readings, the saved automation strategy and
the current recommendation.

Without a facade, the HTTP handler or the React page would have to call
each of them in the right order and stitch the results together. Every new
screen would repeat the same steps, and a change in one query would have to
be fixed in several places.

## Intent

Facade gives one simple entry point over a set of subsystems. It
orchestrates them and leaves them unchanged.

`LocationOverviewFacade.get_overview(location_id)` is that entry point. It
returns one `LocationOverviewDto`.

## Why one entry point

- The overview handler depends on one class, not on five collaborators.
- The order of the calls lives in one place.
- The JSON contract stays stable while the queries behind it can change.
- A test can replace one facade instead of several repositories.

## What it hides

| Subsystem | What the facade asks it |
| --- | --- |
| `OverviewRepository` | location name, device counts by role, latest reading per device |
| `AutomationService` | the recommendation for the location (Strategy, Phase 6) |
| `AutomationRuleRepository` | the saved strategy key when no recommendation exists |

The facade holds no irrigation rule and no SQL. The decision stays in the
strategy classes, sensor translation stays in the adapters, and queries
stay in the repositories.

## Last recommendation

The recommendation is **computed on every request**, not stored. The facade
delegates to `AutomationService.evaluate(location_id)`, so a new reading or
a changed strategy shows up on the next GET. No table stores the last
result.

The `strategy_key` in the overview is the key that evaluation used. A
location with no saved rule shows the default, `conservative`.

## Response

`GET /api/locations/{location_id}/overview`

```json
{
  "location": { "id": "<uuid>", "name": "Lab Site A" },
  "device_counts": { "sensor": 2, "actuator": 2 },
  "latest_readings": [
    { "device_id": "<uuid>", "value": 0.31, "unit": "vwc", "recorded_at": "..." }
  ],
  "strategy_key": "conservative",
  "last_recommendation": { "action": "wait", "reason": "..." }
}
```

A missing location returns 404 with `Location not found.`. Other errors are
not caught by the facade, so a database failure is not reported as a
missing location.

## N+1 note

An N+1 problem would be: load the device list with one query, then run one
more query per device to get its latest reading.

`OverviewRepository.latest_readings` avoids this with a single
`SELECT DISTINCT ON (device_id) ... ORDER BY device_id, recorded_at DESC`
query. It uses the existing index on `(device_id, recorded_at DESC)`.
Device counts use one `GROUP BY role` query.

One overview request runs a fixed number of queries (eight), however many
devices exist.

## Database

No migration and no new table. The facade composes `locations`, `devices`,
`sensor_readings`, `automation_rules` and `zones` from Phases 2–6. No SQL
view was added because the existing tables are enough.

## Where in code

| Role | File |
| --- | --- |
| Overview DTOs | `backend/src/application/overview/dto.py` |
| Facade | `backend/src/application/overview/facade.py` |
| Queries | `backend/src/infrastructure/persistence/overview_repository.py` |
| API route (client of the facade) | `backend/src/interfaces/api/overview.py` |
| Dashboard panel | `frontend/src/features/overview/OverviewPanel.tsx` |
| Integration tests | `backend/tests/test_overview_api.py` |

## Limits of the current version

- `devices` has no `location_id`, so device counts and latest readings
  cover all devices. Only the location, the strategy key and the
  recommendation are scoped by `location_id`.
- The overview shows the latest reading of at most 10 devices, newest
  first.

## Facade and Adapter

The adapters from Phase 5 make one sensor driver fit `SensorPort`. The
facade makes many subsystems simple to call. The facade uses data that the
adapters produced, but it does not translate anything itself.
