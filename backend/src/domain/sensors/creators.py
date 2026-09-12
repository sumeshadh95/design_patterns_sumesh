from __future__ import annotations

from abc import ABC, abstractmethod

from domain.sensors.entity import Sensor


class SensorCreator(ABC):
    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        raise NotImplementedError


class MoistureSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="moisture_sensor",
            display_name=display_name or "Soil moisture sensor",
            default_config={
                "unit": "vwc",
                "sampling_interval_seconds": 300,
                "moisture_threshold": 0.35,
            },
        )


class LightSensorCreator(SensorCreator):
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            device_type="light_sensor",
            display_name=display_name or "Light sensor",
            default_config={
                "unit": "lux",
                "sampling_interval_seconds": 60,
                "brightness_threshold": 200,
            },
        )


def get_creator(sensor_type: str) -> SensorCreator:
    normalized = sensor_type.strip().lower()

    registry: dict[str, SensorCreator] = {
        "moisture": MoistureSensorCreator(),
        "light": LightSensorCreator(),
    }

    if normalized not in registry:
        raise ValueError(f"Unknown sensor type: {sensor_type}")

    return registry[normalized]