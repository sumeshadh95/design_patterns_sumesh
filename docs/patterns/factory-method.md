# Factory Method

## Intent

Factory Method centralizes object creation behind a creator interface so callers do not construct concrete classes directly.

## Application in this project (Phase 2)

- **Product:** `Sensor` domain entity.
- **Concrete creators:** `MoistureSensorCreator`, `LightSensorCreator`.
- **Creator lookup:** `get_creator(type_key)` maps short API keys (`moisture`, `light`) to concrete creators.
- **Client:** `SensorService` resolves creator, asks for prototype sensor, and persists through `DeviceRepository`.

## Why this design is required

- API handlers stay thin and do not instantiate concrete sensor types.
- Type-specific defaults (`default_config`) are defined in one place per sensor type.
- Unknown types fail early with a clear 400 response path.
- The `devices` table stores normalized values such as `device_type="moisture_sensor"` and `role="sensor"`.

## Extension path

To add a new sensor type, add a new concrete creator and one registry entry. Existing service and API flow remain unchanged.
