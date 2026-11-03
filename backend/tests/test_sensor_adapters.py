from uuid import uuid4

import pytest

from domain.devices.entity import Device
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from infrastructure.adapters.sensors.selector import select_sensor_adapter
from infrastructure.adapters.sensors.simulation import (
    LIGHT_RANGE_LUX,
    MOISTURE_RANGE_VWC,
    SimulationSensorAdapter,
)
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


def make_device(
    device_type: str = "moisture_sensor",
    *,
    family: str = "simulation",
    config: dict | None = None,
    persisted: bool = True,
) -> Device:
    return Device(
        id=uuid4() if persisted else None,
        device_type=device_type,
        role="sensor",
        device_family=family,
        display_name="Test sensor",
        default_config=config if config is not None else {"protocol": "simulation"},
    )


def test_vendor_adapter_normalizes_raw_payload() -> None:
    device = make_device(family="edge", config={"vendor_stub": True})

    reading = VendorStubSensorAdapter().read(device)

    assert reading.device_id == device.id
    assert 0.0 <= reading.value <= 1.0
    assert reading.unit == "vwc"
    assert reading.source == "vendor"
    assert reading.recorded_at.tzinfo is not None


def test_vendor_adapter_normalizes_light_sensor() -> None:
    reading = VendorStubSensorAdapter().read(make_device("light_sensor"))

    assert reading.unit == "lux"
    assert reading.source == "vendor"


def test_vendor_adapter_raises_error_for_unknown_type() -> None:
    with pytest.raises(ValueError, match="Unsupported vendor sensor type"):
        VendorStubSensorAdapter().read(make_device("unknown_sensor"))


def test_simulation_adapter_value_in_range() -> None:
    for _ in range(50):
        moisture = SimulationSensorAdapter().read(make_device("moisture_sensor"))
        light = SimulationSensorAdapter().read(make_device("light_sensor"))

        assert MOISTURE_RANGE_VWC[0] <= moisture.value <= MOISTURE_RANGE_VWC[1]
        assert moisture.unit == "vwc"
        assert moisture.source == "simulation"
        assert LIGHT_RANGE_LUX[0] <= light.value <= LIGHT_RANGE_LUX[1]
        assert light.unit == "lux"


def test_simulation_adapter_raises_error_for_unpersisted() -> None:
    with pytest.raises(ValueError, match="Cannot read an unpersisted device"):
        SimulationSensorAdapter().read(make_device(persisted=False))


def test_mqtt_adapter_translates_payload() -> None:
    device = make_device(family="edge", config={"protocol": "mqtt"})

    reading = MqttSensorAdapter().translate(device, {"value": 0.41, "unit": "vwc"})

    assert reading.device_id == device.id
    assert reading.value == 0.41
    assert reading.unit == "vwc"
    assert reading.source == "mqtt"
    assert reading.recorded_at.tzinfo is not None


def test_mqtt_adapter_rejects_bad_payload() -> None:
    device = make_device(family="edge", config={"protocol": "mqtt"})

    with pytest.raises(ValueError, match="numeric 'value'"):
        MqttSensorAdapter().translate(device, {"unit": "vwc"})


def test_selector_uses_protocol_simulation() -> None:
    adapter = select_sensor_adapter(make_device(config={"protocol": "simulation"}))

    assert isinstance(adapter, SimulationSensorAdapter)


def test_selector_uses_vendor_flag() -> None:
    device = make_device(
        family="edge",
        config={"protocol": "simulation", "vendor_stub": True},
    )

    assert isinstance(select_sensor_adapter(device), VendorStubSensorAdapter)


def test_selector_rejects_one_shot_read_for_mqtt() -> None:
    device = make_device(family="edge", config={"protocol": "mqtt"})

    with pytest.raises(ValueError, match="MQTT devices push"):
        select_sensor_adapter(device)


def test_selector_raises_error_for_unknown_protocol() -> None:
    with pytest.raises(ValueError, match="No sensor adapter"):
        select_sensor_adapter(make_device(config={"protocol": "modbus"}))


def test_simulation_actuator_records_command() -> None:
    adapter = SimulationActuatorAdapter()
    device_id = uuid4()

    adapter.apply(
        device_id=device_id,
        command="start_pump",
        payload={"duration_seconds": 30},
    )

    assert adapter.applied_commands == [
        {
            "device_id": str(device_id),
            "command": "start_pump",
            "payload": {"duration_seconds": 30},
        }
    ]
