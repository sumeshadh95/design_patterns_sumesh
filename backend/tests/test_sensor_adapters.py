import pytest
from uuid import uuid4

from domain.devices.entity import Device
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.adapters.sensors.selector import select_sensor_adapter
from infrastructure.adapters.sensors.simulation import SimulationSensorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


def test_vendor_adapter_normalizes_moisture_sensor() -> None:
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="edge",
        display_name="Vendor soil probe",
        default_config={"protocol": "gpio-stub"},
    )
    reading = VendorStubSensorAdapter().read(device)
    assert reading.device_id == device.id
    assert 0.0 <= reading.value <= 1.0
    assert reading.unit == "vwc"
    assert reading.source == "vendor"
    assert reading.recorded_at.tzinfo is not None


def test_vendor_adapter_normalizes_light_sensor() -> None:
    device = Device(
        id=uuid4(),
        device_type="light_sensor",
        role="sensor",
        device_family="edge",
        display_name="Vendor lux meter",
        default_config={"protocol": "gpio-stub"},
    )
    reading = VendorStubSensorAdapter().read(device)
    assert reading.unit == "lux"
    assert reading.source == "vendor"
    assert reading.value >= 0.0


def test_vendor_adapter_raises_error_for_unpersisted_device() -> None:
    device = Device(
        id=None,
        device_type="moisture_sensor",
        role="sensor",
        device_family="edge",
        display_name="Vendor unpersisted",
        default_config={},
    )
    with pytest.raises(ValueError, match="Cannot read an unpersisted device"):
        VendorStubSensorAdapter().read(device)


def test_vendor_adapter_raises_error_for_unknown_type() -> None:
    device = Device(
        id=uuid4(),
        device_type="unknown_sensor",
        role="sensor",
        device_family="edge",
        display_name="Vendor unknown",
        default_config={},
    )
    with pytest.raises(ValueError, match="Unsupported vendor sensor type"):
        VendorStubSensorAdapter().read(device)


def test_simulation_adapter_reads_moisture() -> None:
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Sim moisture",
        default_config={},
    )
    reading = SimulationSensorAdapter().read(device)
    assert reading.device_id == device.id
    assert reading.unit == "vwc"
    assert reading.source == "simulation"


def test_simulation_adapter_reads_light() -> None:
    device = Device(
        id=uuid4(),
        device_type="light_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Sim light",
        default_config={},
    )
    reading = SimulationSensorAdapter().read(device)
    assert reading.unit == "lux"
    assert reading.source == "simulation"


def test_simulation_adapter_raises_error_for_unpersisted() -> None:
    device = Device(
        id=None,
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Sim unpersisted",
        default_config={},
    )
    with pytest.raises(ValueError, match="Cannot read an unpersisted device"):
        SimulationSensorAdapter().read(device)


def test_simulation_adapter_raises_error_for_unknown_type() -> None:
    device = Device(
        id=uuid4(),
        device_type="unknown_type",
        role="sensor",
        device_family="simulation",
        display_name="Sim unknown",
        default_config={},
    )
    with pytest.raises(ValueError, match="Unsupported sensor type"):
        SimulationSensorAdapter().read(device)


def test_selector_chooses_simulation_for_simulation_family() -> None:
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="simulation",
        display_name="Sim family device",
        default_config={},
    )
    adapter = select_sensor_adapter(device)
    assert isinstance(adapter, SimulationSensorAdapter)


def test_selector_chooses_simulation_for_sim_protocol() -> None:
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="unknown",
        display_name="Sim protocol device",
        default_config={"protocol": "sim"},
    )
    adapter = select_sensor_adapter(device)
    assert isinstance(adapter, SimulationSensorAdapter)


def test_selector_chooses_vendor_for_edge_family() -> None:
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="edge",
        display_name="Edge device",
        default_config={},
    )
    adapter = select_sensor_adapter(device)
    assert isinstance(adapter, VendorStubSensorAdapter)


def test_selector_chooses_vendor_for_gpio_stub_protocol() -> None:
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="unknown",
        display_name="GPIO stub device",
        default_config={"protocol": "gpio-stub"},
    )
    adapter = select_sensor_adapter(device)
    assert isinstance(adapter, VendorStubSensorAdapter)


def test_selector_raises_error_for_unknown_family_and_protocol() -> None:
    device = Device(
        id=uuid4(),
        device_type="moisture_sensor",
        role="sensor",
        device_family="unknown",
        display_name="Unknown device",
        default_config={},
    )
    with pytest.raises(ValueError, match="No sensor adapter is configured"):
        select_sensor_adapter(device)


def test_simulation_actuator_records_command() -> None:
    adapter = SimulationActuatorAdapter()
    device_id = uuid4()
    adapter.apply(
        device_id=device_id,
        command="turn_on",
        payload={"duration_seconds": 30},
    )
    assert adapter.applied_commands == [
        {
            "device_id": str(device_id),
            "command": "turn_on",
            "payload": {"duration_seconds": 30},
        }
    ]