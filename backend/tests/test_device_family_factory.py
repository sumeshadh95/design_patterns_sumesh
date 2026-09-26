from domain.devices.family_factory import EdgeHardwareFactory, SimulationDeviceFactory


def test_simulation_factory_returns_four_devices() -> None:
    devices = SimulationDeviceFactory().create_device_set()

    assert len(devices) == 4
    assert all(device.device_family == "simulation" for device in devices)
    assert {device.role for device in devices} == {"sensor", "actuator"}


def test_edge_factory_differs_from_simulation() -> None:
    simulation_devices = SimulationDeviceFactory().create_device_set()
    edge_devices = EdgeHardwareFactory().create_device_set()

    assert all(device.device_family == "simulation" for device in simulation_devices)
    assert all(device.device_family == "edge" for device in edge_devices)

    simulation_protocols = {d.default_config.get("protocol") for d in simulation_devices}
    edge_protocols = {d.default_config.get("protocol") for d in edge_devices}

    assert simulation_protocols != edge_protocols