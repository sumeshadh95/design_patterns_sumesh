from __future__ import annotations

from typing import Any

from domain.locations.entity import Location, LocationConfig, Zone
from domain.locations.errors import ConfigurationError


class LocationConfigBuilder:
    def __init__(self) -> None:
        self._location_name: str | None = None
        self._zones: list[Zone] = []

    def with_location_name(self, name: str) -> "LocationConfigBuilder":
        self._location_name = name.strip()
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict[str, Any] | None = None,
    ) -> "LocationConfigBuilder":
        self._zones.append(
            Zone(
                name=name.strip(),
                moisture_threshold_low=float(moisture_threshold_low),
                moisture_threshold_high=float(moisture_threshold_high),
                schedule=schedule or {},
            )
        )
        return self

    def build(self) -> LocationConfig:
        if not self._location_name:
            raise ConfigurationError("Location name is required.")

        if not self._zones:
            raise ConfigurationError("At least one zone is required.")

        for zone in self._zones:
            if not zone.name:
                raise ConfigurationError("Zone name is required.")

            if not 0.0 <= zone.moisture_threshold_low <= 1.0:
                raise ConfigurationError(
                    "Zone low moisture threshold must be between 0.0 and 1.0."
                )

            if not 0.0 <= zone.moisture_threshold_high <= 1.0:
                raise ConfigurationError(
                    "Zone high moisture threshold must be between 0.0 and 1.0."
                )

            if zone.moisture_threshold_low >= zone.moisture_threshold_high:
                raise ConfigurationError(
                    "Zone low moisture threshold must be lower than its high threshold."
                )

        return LocationConfig(
            location=Location(
                id=None,
                name=self._location_name,
                zones=tuple(self._zones),
            )
        )