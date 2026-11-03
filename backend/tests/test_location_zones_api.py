from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def create_location(*zone_names: str) -> dict:
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": f"Zones Site {uuid4()}",
            "zones": [
                {
                    "name": name,
                    "moisture_threshold_low": 0.2,
                    "moisture_threshold_high": 0.45,
                    "schedule": {},
                }
                for name in (zone_names or ("Bench 1",))
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def create_sensor() -> str:
    response = client.post(
        "/api/sensors",
        json={"type": "moisture", "display_name": f"Zone test {uuid4()}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def zone_id(config: dict, name: str) -> str:
    return next(zone["id"] for zone in config["zones"] if zone["name"] == name)


def assign(device_id: str, target_zone_id: str | None):
    return client.patch(f"/api/devices/{device_id}/zone", json={"zone_id": target_zone_id})


def device(device_id: str) -> dict:
    devices = client.get("/api/devices").json()
    return next(d for d in devices if d["id"] == device_id)


def test_assign_devices_to_zone() -> None:
    config = create_location("Bench 1", "Bench 2")
    location_id = config["location"]["id"]
    zone_1 = zone_id(config, "Bench 1")
    zone_2 = zone_id(config, "Bench 2")
    first, second, other = create_sensor(), create_sensor(), create_sensor()

    assert assign(first, zone_2).status_code == 200
    assert assign(second, zone_2).status_code == 200
    assert assign(other, zone_1).status_code == 200

    listed = client.get(f"/api/locations/{location_id}/zones/{zone_2}/devices")

    assert listed.status_code == 200
    assert {d["id"] for d in listed.json()} == {first, second}
    assert device(first)["zone_id"] == zone_2
    assert device(first)["location_id"] == location_id


def test_unassign_clears_zone_and_location() -> None:
    config = create_location()
    sensor_id = create_sensor()
    assign(sensor_id, zone_id(config, "Bench 1"))

    response = assign(sensor_id, None)

    assert response.status_code == 200
    assert response.json()["zone_id"] is None
    assert response.json()["location_id"] is None


def test_assign_rejects_missing_device_or_zone() -> None:
    config = create_location()

    assert assign(str(uuid4()), zone_id(config, "Bench 1")).status_code == 404
    assert assign(create_sensor(), str(uuid4())).status_code == 404


def test_zone_device_list_rejects_zone_from_other_location() -> None:
    first = create_location()
    second = create_location()

    response = client.get(
        f"/api/locations/{first['location']['id']}"
        f"/zones/{zone_id(second, 'Bench 1')}/devices"
    )

    assert response.status_code == 404


def test_list_locations() -> None:
    first = create_location()
    second = create_location()

    response = client.get("/api/locations")

    assert response.status_code == 200
    ids = [location["id"] for location in response.json()]
    assert first["location"]["id"] in ids
    assert second["location"]["id"] in ids
    # Oldest first: the earlier create comes before the later one.
    assert ids.index(first["location"]["id"]) < ids.index(second["location"]["id"])


def test_delete_location_clears_assignments() -> None:
    doomed = create_location()
    kept = create_location()
    sensor_id = create_sensor()
    assign(sensor_id, zone_id(doomed, "Bench 1"))
    doomed_id = doomed["location"]["id"]

    response = client.delete(f"/api/locations/{doomed_id}")

    assert response.status_code == 204
    assert client.get(f"/api/locations/{doomed_id}/config").status_code == 404
    assert client.get(f"/api/locations/{kept['location']['id']}/config").status_code == 200
    assert device(sensor_id)["zone_id"] is None
    assert device(sensor_id)["location_id"] is None
    assert client.delete(f"/api/locations/{doomed_id}").status_code == 404


def test_add_zone_to_location() -> None:
    config = create_location()
    location_id = config["location"]["id"]

    response = client.post(
        f"/api/locations/{location_id}/zones",
        json={
            "name": "Bench 2",
            "moisture_threshold_low": 0.25,
            "moisture_threshold_high": 0.5,
        },
    )

    assert response.status_code == 201
    assert response.json()["location_id"] == location_id
    names = [z["name"] for z in client.get(f"/api/locations/{location_id}/config").json()["zones"]]
    assert names == ["Bench 1", "Bench 2"]


def test_add_zone_rejects_duplicate_name() -> None:
    config = create_location()

    response = client.post(
        f"/api/locations/{config['location']['id']}/zones",
        json={"name": "bench 1", "moisture_threshold_low": 0.2, "moisture_threshold_high": 0.4},
    )

    assert response.status_code == 400


def test_update_zone_rejects_invalid_thresholds() -> None:
    config = create_location()
    location_id = config["location"]["id"]
    target = zone_id(config, "Bench 1")

    response = client.patch(
        f"/api/locations/{location_id}/zones/{target}",
        json={"name": "Bench 1", "moisture_threshold_low": 0.7, "moisture_threshold_high": 0.4},
    )

    assert response.status_code == 400
    stored = client.get(f"/api/locations/{location_id}/config").json()["zones"][0]
    assert stored["moisture_threshold_low"] == 0.2
    assert stored["moisture_threshold_high"] == 0.45


def test_update_zone_changes_fields() -> None:
    config = create_location()
    location_id = config["location"]["id"]
    target = zone_id(config, "Bench 1")

    response = client.patch(
        f"/api/locations/{location_id}/zones/{target}",
        json={
            "name": "Bench A",
            "moisture_threshold_low": 0.3,
            "moisture_threshold_high": 0.5,
            "schedule": {"watering": "07:00"},
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Bench A"
    assert response.json()["schedule"] == {"watering": "07:00"}


def test_delete_zone_clears_assignments() -> None:
    config = create_location("Bench 1", "Bench 2")
    location_id = config["location"]["id"]
    target = zone_id(config, "Bench 2")
    sensor_id = create_sensor()
    assign(sensor_id, target)

    response = client.delete(f"/api/locations/{location_id}/zones/{target}")

    assert response.status_code == 204
    assert device(sensor_id)["zone_id"] is None
    assert device(sensor_id)["location_id"] is None
    zones = client.get(f"/api/locations/{location_id}/config").json()["zones"]
    assert [z["name"] for z in zones] == ["Bench 1"]


def test_delete_last_zone_is_rejected() -> None:
    config = create_location()
    location_id = config["location"]["id"]
    target = zone_id(config, "Bench 1")

    response = client.delete(f"/api/locations/{location_id}/zones/{target}")

    assert response.status_code == 400
    assert len(client.get(f"/api/locations/{location_id}/config").json()["zones"]) == 1


def test_zone_routes_return_404_for_missing_location() -> None:
    missing = uuid4()
    body = {"name": "X", "moisture_threshold_low": 0.2, "moisture_threshold_high": 0.4}

    assert client.post(f"/api/locations/{missing}/zones", json=body).status_code == 404
    assert client.patch(f"/api/locations/{missing}/zones/{uuid4()}", json=body).status_code == 404
    assert client.delete(f"/api/locations/{missing}/zones/{uuid4()}").status_code == 404
