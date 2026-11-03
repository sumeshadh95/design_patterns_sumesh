from domain.devices.entity import Device
from domain.sensors.ports import SensorPort
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter

VENDOR_STUB_FLAG = "vendor_stub"


def select_sensor_adapter(device: Device) -> SensorPort:
    """Pick the adapter for a one-shot read.

    Rule:
    - default_config.vendor_stub == true -> VendorStubSensorAdapter
      (its own flag, so it never collides with a protocol value)
    - default_config.protocol == "simulation" -> SimulationSensorAdapter
    - default_config.protocol == "mqtt" -> no one-shot read; the device pushes
      payloads that MqttSensorAdapter.translate turns into readings
    """
    if device.default_config.get(VENDOR_STUB_FLAG) is True:
        return VendorStubSensorAdapter()

    if device.protocol == "simulation":
        return SimulationSensorAdapter()

    if device.protocol == "mqtt":
        raise ValueError(
            "MQTT devices push their readings; a one-shot read is not available."
        )

    raise ValueError(
        f"No sensor adapter is configured for protocol '{device.protocol}'."
    )
