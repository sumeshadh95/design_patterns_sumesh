# Adapter

## Intent

Adapter translates incompatible external or simulated device APIs into a unified interface that the application can use without depending on vendor-specific details.

## Problem

Different sensor sources produce different payload shapes. The simulation generates a value in code, a vendor SDK returns nested fields with other names, and an MQTT device sends a small JSON payload. If application services or API routers used those shapes directly, vendor details would spread through the codebase.

## Solution

The domain defines `SensorPort`, which returns a normalized `Reading` containing `device_id`, `value`, `unit`, `source` and `recorded_at`.

| Adapter | Raw shape | `source` |
| --- | --- | --- |
| `SimulationSensorAdapter` | Generated in code: moisture `0.2`–`0.6` vwc, light `200`–`2000` lux | `simulation` |
| `VendorStubSensorAdapter` | Nested payload: `kind`, `measurement.fraction` / `illuminance`, `captured_at` | `vendor` |
| `MqttSensorAdapter.translate` | Payload dict such as `{"value": 0.41, "unit": "vwc"}` | `mqtt` |

`MqttSensorAdapter` only translates a dict. It opens no broker connection; Phase 12 delivers the dict over device HTTP or an optional broker.

`ActuatorPort` defines the unified actuator operation. `SimulationActuatorAdapter` is a log-only, in-memory implementation that Phase 9 wraps with decorators.

## Adapter selection

`select_sensor_adapter` uses `default_config`:

- `vendor_stub: true` selects `VendorStubSensorAdapter`. It is a separate flag, so it never collides with a protocol value.
- `protocol: "simulation"` selects `SimulationSensorAdapter`.
- `protocol: "mqtt"` has no one-shot read; the device pushes payloads that `MqttSensorAdapter.translate` turns into readings. A `POST /read` on such a device returns 400.

The simulation family uses `protocol: "simulation"`. The edge family is the real-device kit and uses `protocol: "mqtt"`. A migration converted the earlier values (`sim` and `gpio-stub`) to these.

## One ingest path

`ReadingIngest` is the only writer of `sensor_readings`:

- `take_reading(device_id)` selects an adapter, reads, stores and returns a `ReadingDto` (used by `POST /api/sensors/{id}/read` and the sampler);
- `record(device_id, reading)` stores a reading another adapter already translated, such as MQTT output (Phase 12 will call it);
- `list_readings(device_id, limit)` returns stored history.

## Sampling

`devices.sampling_interval_seconds` (default 300, minimum 5) and `devices.tracking_enabled` (default true) are columns, backfilled from `default_config` when the JSON already had a numeric interval. `PATCH /api/devices/{id}/sampling` updates them.

`SimulationSampler.run_once(now)` loads sensors with `protocol` `simulation` and tracking on, and records a reading when there is no previous row or the device's interval has elapsed. MQTT devices and tracking-off devices are skipped. The app lifespan runs it every few seconds; tests call `run_once` with a fake clock.

## Where it lives

- Domain ports and reading: `domain/sensors/ports.py`, `domain/sensors/reading.py`, `domain/actuators/ports.py`
- Infrastructure adapters: `infrastructure/adapters/sensors/` (`simulation.py`, `vendor_stub.py`, `mqtt.py`, `selector.py`) and `infrastructure/adapters/actuators/simulation.py`
- Ingest and sampler: `application/readings/service.py`, `application/readings/sampler.py`
- Sampling settings: `application/devices/sampling_service.py`, `domain/devices/sampling.py`
- Persistence: `infrastructure/persistence/reading_repository.py`
- API: `interfaces/api/sensors.py`, `interfaces/api/devices.py`

## Why readings are persisted

Every successful read is appended to `sensor_readings`. This preserves history across restarts and gives Phase 6 Strategy and the Phase 7 overview real stored readings, whether they came from a manual read, the sampler or MQTT.

## Extension idea

Add a third adapter for a Modbus or cloud-vendor sensor. Only the new adapter and the selector need to understand its raw protocol; the ingest service, reading DTO, API and database schema remain unchanged.
