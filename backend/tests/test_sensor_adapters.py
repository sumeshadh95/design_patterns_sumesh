from uuid import uuid4

from domain.devices.entity import Device
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter
from infrastructure.adapters.sensors.vendor_stub import VendorStubSensorAdapter


def test_vendor_adapter_normalizes_raw_payload() -> None:
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
    assert reading.value == 0.37
    assert reading.unit == "vwc"
    assert reading.source == "vendor"
    assert reading.recorded_at.tzinfo is not None


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