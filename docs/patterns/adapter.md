# Adapter

## Intent

Adapter translates incompatible external or simulated device APIs into a unified interface that the application can use without depending on vendor-specific details.

## Problem

Different sensor drivers can return different payload shapes. A simulation driver may expose a direct value, while a vendor SDK may return nested fields with different names. If application services or API routers use those vendor-shaped values directly, vendor details spread through the codebase.

## Solution

The domain defines `SensorPort`, which returns a normalized `Reading` containing `device_id`, `value`, `unit`, `source`, and `recorded_at`.

`SimulationSensorAdapter` and `VendorStubSensorAdapter` both implement `SensorPort`. The vendor adapter translates its nested raw payload into the same normalized `Reading` returned by the simulation adapter.

`ActuatorPort` defines the unified actuator operation. `SimulationActuatorAdapter` is a log-only/in-memory implementation that Phase 9 can wrap with decorators.

## Adapter selection

The selector uses `device_family` and the device configuration protocol:

- `simulation` family or `sim` protocol uses `SimulationSensorAdapter`.
- `edge` family or `gpio-stub` protocol uses `VendorStubSensorAdapter`.

## Where it lives

- Domain ports and reading: `domain/sensors/ports.py`, `domain/sensors/reading.py`, and `domain/actuators/ports.py`
- Infrastructure adapters: `infrastructure/adapters/`
- Reading persistence: `infrastructure/persistence/reading_repository.py`
- Use case: `application/readings/service.py`
- API: `interfaces/api/sensors.py`

## Why readings are persisted

Every successful read is appended to `sensor_readings`. This preserves history across browser refreshes and gives Phase 6 Strategy a real latest reading to evaluate against zone thresholds.

## Extension idea

Add a third adapter for a Modbus or cloud-vendor sensor. Only the new adapter and selector need to understand its raw protocol; the application service, reading DTO, API, and database schema remain unchanged.