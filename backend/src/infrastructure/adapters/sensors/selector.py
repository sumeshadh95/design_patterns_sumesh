from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


def select_sensor_adapter(device: Device) -> SensorPort:
    protocol = str(device.default_config.get("protocol", ""))

    if device.device_family == "simulation" or protocol == "sim":
        return SimulationSensorAdapter()

    if device.device_family == "edge" or protocol == "gpio-stub":
        return VendorStubSensorAdapter()

    raise ValueError(
        f"No sensor adapter is configured for device family '{device.device_family}'."
    )