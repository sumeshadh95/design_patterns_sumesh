from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.devices.entity import Device
from domain.sensors.entity import Sensor
from infrastructure.persistence.models import DeviceRow


class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_sensor(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            device_family="simulation",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)

        sensor.id = row.id
        return sensor

    def list_sensors(self) -> list[Sensor]:
        rows = (
            self.session.execute(
                select(DeviceRow)
                .where(DeviceRow.role == "sensor")
                .order_by(DeviceRow.created_at.desc())
            )
            .scalars()
            .all()
        )

        return [
            Sensor(
                id=row.id,
                device_type=row.device_type,
                display_name=row.display_name,
                default_config=row.default_config,
            )
            for row in rows
        ]

    def save_device(self, device: Device) -> Device:
        row = DeviceRow(
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._row_to_device(row)

    def save_devices(self, devices: list[Device]) -> list[Device]:
        rows = [
            DeviceRow(
                device_type=device.device_type,
                role=device.role,
                device_family=device.device_family,
                display_name=device.display_name,
                default_config=device.default_config,
            )
            for device in devices
        ]
        self.session.add_all(rows)
        self.session.commit()
        for row in rows:
            self.session.refresh(row)

        return [self._row_to_device(row) for row in rows]

    def get_device(self, device_id) -> Device | None:
        row = self.session.get(DeviceRow, device_id)

        if row is None:
            return None

        return self._row_to_device(row)

    def list_devices(
        self,
        *,
        device_family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        stmt = select(DeviceRow)

        if device_family:
            stmt = stmt.where(DeviceRow.device_family == device_family)

        if role:
            stmt = stmt.where(DeviceRow.role == role)

        rows = (
            self.session.execute(stmt.order_by(DeviceRow.created_at.desc()))
            .scalars()
            .all()
        )

        return [self._row_to_device(row) for row in rows]

    @staticmethod
    def _row_to_device(row: DeviceRow) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name or row.device_type,
            default_config=row.default_config,
        )