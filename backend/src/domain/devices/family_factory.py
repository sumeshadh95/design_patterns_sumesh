from __future__ import annotations

from abc import ABC, abstractmethod

from domain.devices.entity import Device
from domain.sensors.creators import LightSensorCreator, MoistureSensorCreator
from domain.sensors.entity import Sensor


def _sensor_to_device(sensor: Sensor, family: str, protocol: str) -> Device:
    config = dict(sensor.default_config)
    config["protocol"] = protocol

    return Device(
        id=None,
        device_type=sensor.device_type,
        role="sensor",
        device_family=family,
        display_name=sensor.display_name or sensor.device_type,
        default_config=config,
    )


class DeviceFamilyFactory(ABC):
    @property
    @abstractmethod
    def family_key(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def create_device_set(self) -> list[Device]:
        raise NotImplementedError


class SimulationDeviceFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "simulation"

    def create_device_set(self) -> list[Device]:
        moisture = MoistureSensorCreator().create_sensor("Sim soil moisture sensor")
        light = LightSensorCreator().create_sensor("Sim ambient light sensor")

        return [
            _sensor_to_device(moisture, family=self.family_key, protocol="sim"),
            _sensor_to_device(light, family=self.family_key, protocol="sim"),
            Device(
                id=None,
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Sim irrigation pump",
                default_config={"protocol": "sim", "max_flow_lpm": 18},
            ),
            Device(
                id=None,
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Sim grow light",
                default_config={"protocol": "sim", "spectrum": "full"},
            ),
        ]


class EdgeHardwareFactory(DeviceFamilyFactory):
    @property
    def family_key(self) -> str:
        return "edge"

    def create_device_set(self) -> list[Device]:
        moisture = MoistureSensorCreator().create_sensor("Edge soil moisture probe")
        light = LightSensorCreator().create_sensor("Edge lux sensor")

        return [
            _sensor_to_device(moisture, family=self.family_key, protocol="gpio-stub"),
            _sensor_to_device(light, family=self.family_key, protocol="gpio-stub"),
            Device(
                id=None,
                device_type="water_pump",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge irrigation pump",
                default_config={"protocol": "gpio-stub", "pin": 17},
            ),
            Device(
                id=None,
                device_type="grow_light",
                role="actuator",
                device_family=self.family_key,
                display_name="Edge grow light",
                default_config={"protocol": "gpio-stub", "pin": 27},
            ),
        ]


def get_family_factory(family: str) -> DeviceFamilyFactory:
    normalized = family.strip().lower()
    registry: dict[str, DeviceFamilyFactory] = {
        "simulation": SimulationDeviceFactory(),
        "edge": EdgeHardwareFactory(),
    }

    if normalized not in registry:
        raise ValueError(f"Unknown device family: {family}")

    return registry[normalized]