# Observer — Event Bus and Alerts

## Problem

When a reading is stored, a command fails or an actuator enters `error`,
several reactions may follow: check the zone's moisture threshold, store an
alert, and later push the change to the dashboard. If `ReadingIngest`,
`CommandService` and the transition service called each reaction directly,
every new reaction would change the producers, and the reading path would
depend on the alerts table.

## Intent

Observer sets up a one-to-many dependency: when something happens, one
publish reaches every interested subscriber. The publisher only knows the
bus and the event, not who listens.

## Participants

| Role | In this application |
| --- | --- |
| Subject / event bus | `EventBus` in `domain/events/bus.py` (`subscribe`, `publish`) |
| Events | `ReadingCreated`, `ThresholdCrossed`, `CommandFailed`, `ActuatorStateChanged` |
| Publishers | `ReadingIngest`, `CommandService`, the transition service (`ActuatorStateService.transition`) |
| Concrete observers | `MoistureThresholdSubscriber`, `AlertPersistenceSubscriber` |
| Composition root | `build_event_bus` in `application/event_bus.py` |

## Subject vs subscribers

The subject keeps a list of handlers per event class and calls them in
subscription order. It has no idea what they do. Subscribers decide their own
reaction:

| Event | Published by | Subscriber | Result |
| --- | --- | --- | --- |
| `reading.created` | `ReadingIngest`, after insert, only if `tracking_enabled` | `MoistureThresholdSubscriber` | publishes `threshold.crossed` when unit is `vwc`, zone is set and value < zone low |
| `threshold.crossed` | `MoistureThresholdSubscriber` | `AlertPersistenceSubscriber` | alert: warning, `Moisture below zone low` |
| `command.failed` | `CommandService`, when a decorator blocks | `AlertPersistenceSubscriber` | alert: warning, the failure message |
| `state.changed` | every successful state save | `AlertPersistenceSubscriber` | alert only for `error`: critical, `Actuator entered error` |

Publishers never import `AlertRepository`; only `AlertPersistenceSubscriber`
writes the `alerts` table.

## One ingest, one publish rule

Manual read (`POST /api/sensors/{id}/read`), the simulation sampler and an
MQTT payload translated by `MqttSensorAdapter` all store readings through
`ReadingIngest._persist`, which publishes `reading.created`. A device with
`tracking_enabled` false still gets its reading row, but no event.

`location_id` and `zone_id` are copied from the device at publish time. For
an unassigned device both stay null, so no zone is invented and no threshold
check runs.

## One bus

`application/event_bus.py` builds one `EventBus`, subscribes both
subscribers, and the routers and the sampler inject that same bus into the
publishers. Subscribers open their own short database session per event.

A failing handler is logged, and the handlers after it still run, so a broken
alert writer cannot block other subscribers.

## Alerts

| Column | Type |
| --- | --- |
| `id` | UUID primary key |
| `location_id` | UUID, FK to `locations`, nullable, `ON DELETE SET NULL` |
| `zone_id` | UUID, FK to `zones`, nullable, `ON DELETE SET NULL` |
| `device_id` | UUID, FK to `devices`, nullable, `ON DELETE SET NULL` |
| `severity` | `info`, `warning` or `critical` |
| `message` | TEXT |
| `event_type` | e.g. `threshold.crossed`, `command.failed`, `state.changed` |
| `status` | `active` or `resolved` |
| `created_at` | timestamptz |
| `acknowledged_at` | timestamptz, nullable (not in the API response) |

## API

`GET /api/alerts?status=active&location_id=&zone_id=&since=&limit=50`

Newest first. `status` is `active` (default), `resolved` or `all`; anything
else is 400. `limit` is 1–200. `since` keeps alerts created at or after it.

```json
{
  "id": "<uuid>",
  "location_id": "<uuid>",
  "zone_id": "<uuid>",
  "device_id": "<uuid>",
  "severity": "warning",
  "message": "Moisture below zone low",
  "event_type": "threshold.crossed",
  "status": "active",
  "created_at": "..."
}
```

## Dashboard

The Event feed (`#events`) polls `GET /api/alerts` every 5 seconds, can filter
by location and zone, shows a severity badge per alert and has an empty state.
Alerts come from the database, so they survive a page refresh.

## Observer vs the Phase 12 WebSocket

In this phase the feed polls, and `frontend/src/services/realtime.ts` is only
a stub (`RealtimeEvent`, `subscribeRealtime` returning an unsubscribe
function). Phase 12 adds a WebSocket as one more subscriber on this same bus;
the socket only forwards events, it does not get its own pub/sub. The
publishers stay unchanged.

## Where in code

| Role | File |
| --- | --- |
| Events | `backend/src/domain/events/events.py` |
| Event bus | `backend/src/domain/events/bus.py` |
| Subscribers | `backend/src/application/alerts/subscribers.py` |
| Composition root | `backend/src/application/event_bus.py` |
| Alert DTO and list service | `backend/src/application/alerts/dto.py`, `service.py` |
| `AlertRow` | `backend/src/infrastructure/persistence/models.py` |
| Repository | `backend/src/infrastructure/persistence/alert_repository.py` |
| Publishers | `application/readings/service.py`, `application/commands/service.py`, `application/devices/actuator_state_service.py` |
| API | `backend/src/interfaces/api/alerts.py` |
| Event feed | `frontend/src/components/alerts/EventFeed.tsx` |
| Realtime stub | `frontend/src/services/realtime.ts` |
| Tests | `backend/tests/test_event_bus.py`, `backend/tests/test_alerts_api.py` |
