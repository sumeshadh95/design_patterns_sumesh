# Abstract Factory

## Intent

Create coherent, compatible sets of devices (a "family") through a family-level factory so callers receive a kit that shares protocol, defaults, and labels.

## Problem

When related products are selected independently, mismatches may occur: for example a simulated sensor with an edge-only actuator protocol. Scattered `if/elif` creation logic duplicates rules and increases the chance of inconsistent kits.

## Solution

Define an abstract family factory (`DeviceFamilyFactory`) with concrete implementations (e.g., `SimulationDeviceFactory`, `EdgeHardwareFactory`) that return `create_device_set()` — a list of domain `Device` instances. Family factories compose existing single-product creators (Factory Method) to produce each kit member, then tag them with `device_family` and family-specific defaults.

## Factory Method versus Abstract Factory

Factory Method answers, "which one product should be created?" In this application, the Phase 2 `MoistureSensorCreator` and `LightSensorCreator` each create one sensor type.

Abstract Factory answers, "which product line should be created together?" Here, a device-family factory produces a coherent simulation or edge kit containing compatible sensors and actuators. Abstract Factory uses the existing Factory Method creators internally, then applies the selected family's labels, protocol, and defaults.

## Where it lives in code

- Domain: `domain/devices/family_factory.py`, `domain/devices/entity.py`
- Application: `application/devices/family_service.py`, `application/devices/mappers.py`, `application/devices/dto.py`
- Infrastructure: `persistence/models.py` (adds `device_family`), `persistence/device_repository.py`
- API: `interfaces/api/devices.py`

## Why Device is not a DTO

`Device` is a domain entity used by factories, services, and repositories. It models a device independently of HTTP and must not depend on FastAPI or Pydantic.

`DeviceDto` is the API response model used for JSON responses and the Scalar/OpenAPI schema. The dedicated mapper converts a persisted `Device` to `DeviceDto` at the API boundary. Keeping them separate prevents HTTP concerns from leaking into the domain layer.

## Why not delete Factory Method creators

Family factories should reuse the Phase 2 sensor creators for sensor members of the kit. This preserves single-responsibility, makes sensor defaults changeable in one place, and improves testability.

## Extension exercise

Add a third family `field-test` that uses a different protocol and slightly different default thresholds. Implement its factory and register it in the lookup.
