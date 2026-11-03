# Facade — Location Overview

## Problem

The dashboard overview needs data from several subsystems: the location and
its zones, the devices assigned to those zones, the latest sensor readings,
the saved automation strategy and the current recommendation.

Without a facade, the HTTP handler or the React page would have to call each
of them in the right order and stitch the results together. Every new screen
would repeat the same steps, and a change in one query would have to be fixed
in several places.

## Intent

Facade gives one simple entry point over a set of subsystems. It orchestrates
them and leaves them unchanged.

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
| `OverviewRepository` | the location, its zones, and the newest reading per device |
| `DeviceRepository` | the devices assigned to this location (a `zone_id` is set) |
| `AutomationRuleRepository` | the saved strategy key |
| `AutomationService` | the recommendation (Strategy, Phase 6), only when a key is saved |

The facade holds no irrigation rule and no SQL. The decision stays in the
strategy classes, sensor translation stays in the adapters, and queries stay
in the repositories.

## Response

`GET /api/locations/{location_id}/overview`

```json
{
  "location": { "id": "<uuid>", "name": "Lab Site A" },
  "device_counts": { "sensor": 1, "actuator": 0 },
  "zones": [
    {
      "id": "<uuid>",
      "name": "Bench 1",
      "moisture_threshold_low": 0.2,
      "moisture_threshold_high": 0.45,
      "devices": [
        { "id": "<uuid>", "device_type": "moisture_sensor", "role": "sensor", "display_name": "Bench moisture" }
      ],
      "latest_readings": [
        { "device_id": "<uuid>", "value": 0.31, "unit": "vwc", "recorded_at": "...", "tracking_enabled": true, "sampling_interval_seconds": 300 }
      ]
    },
    { "id": "<uuid>", "name": "Bench 2", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6, "devices": [], "latest_readings": [] }
  ],
  "strategy_key": "conservative",
  "last_recommendation": { "action": "wait", "reason": "No zone needs water." }
}
```

- Every zone is listed, including a zone with no devices.
- Only **assigned** devices count: this `location_id` and a non-null
  `zone_id`. Unassigned devices are absent from `device_counts`, `devices`
  and `latest_readings`.
- A device with no reading stays in `devices` and is left out of
  `latest_readings`.
- `tracking_enabled` and `sampling_interval_seconds` on a reading come from
  the device.
- Readings are the newest row per device by `recorded_at`, whether it came
  from a manual read, the sampler or MQTT.
- A missing location returns 404. No saved strategy is still 200, with
  `strategy_key` and `last_recommendation` both `null`.

## Last recommendation

The recommendation is **computed on every request**, not stored. When a key
is saved, the facade calls `AutomationService.evaluate(location_id)`, which
calls `decide` for each zone. The facade does not call the evaluate HTTP
route and does not re-implement the policy. No table stores the result.

## Query shape and N+1

One overview request runs:

1. one load of the location and one of its zones;
2. one query for the devices assigned to the location;
3. one `SELECT DISTINCT ON (device_id) ... ORDER BY device_id, recorded_at DESC`
   query for the newest reading of exactly those device ids;
4. one read of the saved strategy key;
5. evaluate, only when a key is saved.

There is no reading query per device. Device counts are computed from the
device list already loaded. The only per-zone lookups are inside
`AutomationService.evaluate`, which loads the newest moisture and light
reading once per zone. That stays in the strategy service on purpose instead
of re-implementing `decide` in the facade.

## Database

No migration and no new table. The facade composes `locations`, `zones`,
`devices`, `sensor_readings` and `automation_rules`. No SQL view was added
because the existing tables are enough.

## Dashboard

The Overview section has a location dropdown filled from `GET /api/locations`.
Selecting a location makes one `fetchOverview(locationId)` call, and Refresh
repeats that same call. The cards are built only from that response.

## Where in code

| Role | File |
| --- | --- |
| Overview DTOs | `backend/src/application/overview/dto.py` |
| Facade | `backend/src/application/overview/facade.py` |
| Queries | `backend/src/infrastructure/persistence/overview_repository.py`, `device_repository.py` |
| API route (client of the facade) | `backend/src/interfaces/api/overview.py` |
| Dashboard panel | `frontend/src/features/overview/OverviewPanel.tsx` |
| Integration tests | `backend/tests/test_overview_api.py` |

## Facade and Adapter

The adapters from Phase 5 make one sensor source fit `SensorPort`. The facade
makes many subsystems simple to call. The facade shows readings the adapters
produced, but it does not translate anything itself.
