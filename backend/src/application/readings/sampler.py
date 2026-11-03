from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID

from domain.devices.entity import Device

logger = logging.getLogger(__name__)


class TrackedSensorSource(Protocol):
    def list_tracked_simulation_sensors(self) -> list[Device]: ...


class LatestReadingSource(Protocol):
    def latest_recorded_at(self, device_ids: list[UUID]) -> dict[UUID, datetime]: ...


class Ingest(Protocol):
    def take_reading(self, device_id: UUID) -> object: ...


class SimulationSampler:
    """Records readings for simulation sensors whose interval has elapsed.

    Only protocol=simulation sensors with tracking_enabled are loaded, so MQTT
    devices and tracking-off devices never get sampler rows.
    """

    def __init__(
        self,
        devices: TrackedSensorSource,
        readings: LatestReadingSource,
        ingest: Ingest,
    ):
        self._devices = devices
        self._readings = readings
        self._ingest = ingest

    def run_once(self, now: datetime) -> int:
        sensors = self._devices.list_tracked_simulation_sensors()
        last_seen = self._readings.latest_recorded_at(
            [sensor.id for sensor in sensors if sensor.id is not None]
        )
        recorded = 0

        for sensor in sensors:
            if sensor.id is None:
                continue

            last = last_seen.get(sensor.id)
            due = (
                last is None
                or (now - last).total_seconds() >= sensor.sampling_interval_seconds
            )

            if due:
                self._ingest.take_reading(sensor.id)
                recorded += 1

        return recorded


def run_sampler_tick() -> int:
    """One sampler pass with its own database session."""
    from application.readings.service import ReadingIngest
    from infrastructure.db import SessionLocal
    from infrastructure.persistence.device_repository import DeviceRepository
    from infrastructure.persistence.reading_repository import ReadingRepository

    with SessionLocal() as session:
        devices = DeviceRepository(session)
        readings = ReadingRepository(session)
        sampler = SimulationSampler(
            devices,
            readings,
            ReadingIngest(devices, readings),
        )
        return sampler.run_once(datetime.now(timezone.utc))


async def sampler_loop(tick_seconds: float) -> None:
    """Started from the FastAPI lifespan; cancelled on shutdown."""
    while True:
        try:
            await asyncio.to_thread(run_sampler_tick)
        except Exception:
            logger.exception("Simulation sampler tick failed")

        await asyncio.sleep(tick_seconds)
