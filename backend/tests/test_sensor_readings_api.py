from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_read_inserts_sensor_reading() -> None:
    create_response = client.post(
        "/api/sensors",
        json={
            "type": "moisture",
            "display_name": f"Reading test {uuid4()}",
        },
    )

    assert create_response.status_code == 201

    sensor_id = create_response.json()["id"]

    read_response = client.post(f"/api/sensors/{sensor_id}/read")

    assert read_response.status_code == 200

    reading = read_response.json()

    assert reading["device_id"] == sensor_id
    assert reading["unit"] == "vwc"
    assert reading["source"] == "simulation"

    history_response = client.get(
        f"/api/sensors/{sensor_id}/readings?limit=10"
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 1
    assert history[0]["device_id"] == sensor_id


def test_read_missing_sensor_returns_404() -> None:
    response = client.post(f"/api/sensors/{uuid4()}/read")

    assert response.status_code == 404