from __future__ import annotations

from uuid import UUID

from application.readings.dto import ReadingDto
from domain.sensors.reading import Reading
from infrastructure.adapters.sensors.selector import select_sensor_adapter
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.reading_repository import ReadingRepository


class ReadingService:
    def __init__(
        self,
        device_repository: DeviceRepository,
        reading_repository: ReadingRepository,
    ):
        self._device_repository = device_repository
        self._reading_repository = reading_repository

    def take_reading(self, device_id: UUID) -> ReadingDto:
        device = self._device_repository.get_device(device_id)

        if device is None:
            raise LookupError("Sensor device not found.")

        if device.role != "sensor":
            raise ValueError("Readings can only be taken from sensor devices.")

        adapter = select_sensor_adapter(device)
        reading = adapter.read(device)
        saved_reading = self._reading_repository.insert(reading)

        return self._to_dto(saved_reading)

    def list_readings(
        self,
        device_id: UUID,
        limit: int = 20,
    ) -> list[ReadingDto]:
        device = self._device_repository.get_device(device_id)

        if device is None:
            raise LookupError("Sensor device not found.")

        readings = self._reading_repository.list_for_device(
            device_id=device_id,
            limit=limit,
        )

        return [self._to_dto(reading) for reading in readings]

    @staticmethod
    def _to_dto(reading: Reading) -> ReadingDto:
        return ReadingDto(
            device_id=reading.device_id,
            value=reading.value,
            unit=reading.unit,
            source=reading.source,
            recorded_at=reading.recorded_at,
        )