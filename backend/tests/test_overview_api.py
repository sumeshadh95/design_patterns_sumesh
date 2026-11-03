from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_overview_returns_strategy_and_readings() -> None:
    # Seed: a location with two zones, one assigned sensor with a reading,
    # and one unassigned sensor.
    assert client.get(f"/api/locations/{uuid4()}/overview").status_code == 404

    location_name = f"Overview Site {uuid4()}"
    config = client.post(
        "/api/locations/config",
        json={
            "location_name": location_name,
            "zones": [
                {"name": "Bench 1", "moisture_threshold_low": 0.1, "moisture_threshold_high": 0.9},
                {"name": "Bench 2", "moisture_threshold_low": 0.3, "moisture_threshold_high": 0.6},
            ],
        },
    ).json()
    location_id = config["location"]["id"]
    bench_1, bench_2 = (zone["id"] for zone in config["zones"])

    assigned = client.post("/api/sensors", json={"type": "moisture"}).json()["id"]
    unassigned = client.post("/api/sensors", json={"type": "moisture"}).json()["id"]
    client.patch(f"/api/devices/{assigned}/zone", json={"zone_id": bench_1})
    client.post(f"/api/sensors/{assigned}/read")
    client.post(f"/api/sensors/{unassigned}/read")

    response = client.get(f"/api/locations/{location_id}/overview")

    assert response.status_code == 200
    overview = response.json()
    assert overview["location"] == {"id": location_id, "name": location_name}
    assert overview["strategy_key"] is None
    assert overview["last_recommendation"] is None
    assert overview["device_counts"] == {"sensor": 1, "actuator": 0}

    zones = {zone["id"]: zone for zone in overview["zones"]}
    assert set(zones) == {bench_1, bench_2}
    all_device_ids = {d["id"] for zone in overview["zones"] for d in zone["devices"]}
    assert unassigned not in all_device_ids

    reading = zones[bench_1]["latest_readings"][0]
    assert reading["device_id"] == assigned
    assert reading["unit"] == "vwc"
    assert isinstance(reading["value"], float)
    assert reading["tracking_enabled"] is True
    assert reading["sampling_interval_seconds"] == 300

    assert zones[bench_2]["devices"] == []
    assert zones[bench_2]["latest_readings"] == []

    client.put(
        f"/api/locations/{location_id}/automation",
        json={"strategy_key": "aggressive"},
    )
    evaluated = client.post(f"/api/locations/{location_id}/automation/evaluate").json()
    after = client.get(f"/api/locations/{location_id}/overview").json()

    assert after["strategy_key"] == "aggressive"
    assert after["last_recommendation"] == {
        "action": evaluated["action"],
        "reason": evaluated["reason"],
    }


def test_overview_device_without_reading_stays_in_devices() -> None:
    config = client.post(
        "/api/locations/config",
        json={
            "location_name": f"Overview Site {uuid4()}",
            "zones": [{"name": "Bench 1", "moisture_threshold_low": 0.2, "moisture_threshold_high": 0.4}],
        },
    ).json()
    # An edge (MQTT) sensor: the sampler never generates readings for it.
    edge_kit = client.post("/api/devices/provision?family=edge").json()
    sensor_id = next(d["id"] for d in edge_kit if d["device_type"] == "light_sensor")
    client.patch(f"/api/devices/{sensor_id}/zone", json={"zone_id": config["zones"][0]["id"]})

    zone = client.get(f"/api/locations/{config['location']['id']}/overview").json()["zones"][0]

    assert [d["id"] for d in zone["devices"]] == [sensor_id]
    assert zone["latest_readings"] == []
