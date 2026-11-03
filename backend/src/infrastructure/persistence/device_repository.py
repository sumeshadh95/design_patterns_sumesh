from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
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
            sampling_interval_seconds=int(
                sensor.default_config.get("sampling_interval_seconds", 300)
            ),
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
        row = self._new_row(device)
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._row_to_device(row)

    def save_devices(self, devices: list[Device]) -> list[Device]:
        rows = [self._new_row(device) for device in devices]
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

    def list_in_zone(self, zone_id: UUID) -> list[Device]:
        rows = (
            self.session.execute(
                select(DeviceRow)
                .where(DeviceRow.zone_id == zone_id)
                .order_by(DeviceRow.role, DeviceRow.display_name)
            )
            .scalars()
            .all()
        )

        return [self._row_to_device(row) for row in rows]

    def list_assigned_in_location(self, location_id: UUID) -> list[Device]:
        rows = (
            self.session.execute(
                select(DeviceRow)
                .where(
                    DeviceRow.location_id == location_id,
                    DeviceRow.zone_id.is_not(None),
                )
                .order_by(DeviceRow.role, DeviceRow.display_name)
            )
            .scalars()
            .all()
        )

        return [self._row_to_device(row) for row in rows]

    def list_tracked_simulation_sensors(self) -> list[Device]:
        rows = (
            self.session.execute(
                select(DeviceRow).where(
                    DeviceRow.role == "sensor",
                    DeviceRow.tracking_enabled.is_(True),
                    DeviceRow.default_config["protocol"].astext == "simulation",
                )
            )
            .scalars()
            .all()
        )

        return [self._row_to_device(row) for row in rows]

    def set_zone(
        self,
        device_id: UUID,
        zone_id: UUID | None,
        location_id: UUID | None,
    ) -> Device | None:
        row = self.session.get(DeviceRow, device_id)

        if row is None:
            return None

        # zone_id and location_id are always written together.
        row.zone_id = zone_id
        row.location_id = location_id
        self.session.commit()
        self.session.refresh(row)

        return self._row_to_device(row)

    def clear_zone_assignments(self, zone_id: UUID) -> None:
        # No commit here: the caller deletes the zone in the same transaction.
        self.session.execute(
            update(DeviceRow)
            .where(DeviceRow.zone_id == zone_id)
            .values(zone_id=None, location_id=None)
        )

    def set_sampling(
        self,
        device_id: UUID,
        sampling_interval_seconds: int,
        tracking_enabled: bool,
    ) -> Device | None:
        row = self.session.get(DeviceRow, device_id)

        if row is None:
            return None

        row.sampling_interval_seconds = sampling_interval_seconds
        row.tracking_enabled = tracking_enabled
        self.session.commit()
        self.session.refresh(row)

        return self._row_to_device(row)

    @staticmethod
    def _new_row(device: Device) -> DeviceRow:
        return DeviceRow(
            device_type=device.device_type,
            role=device.role,
            device_family=device.device_family,
            display_name=device.display_name,
            default_config=device.default_config,
            sampling_interval_seconds=device.sampling_interval_seconds,
            tracking_enabled=device.tracking_enabled,
        )

    @staticmethod
    def _row_to_device(row: DeviceRow) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name or row.device_type,
            default_config=row.default_config,
            zone_id=row.zone_id,
            location_id=row.location_id,
            sampling_interval_seconds=row.sampling_interval_seconds,
            tracking_enabled=row.tracking_enabled,
        )
