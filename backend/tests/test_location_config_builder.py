import pytest

from domain.locations.config_builder import LocationConfigBuilder
from domain.locations.errors import ConfigurationError


def test_build_success() -> None:
    config = (
        LocationConfigBuilder()
        .with_location_name("Lab Site A")
        .add_zone(
            name="Bench 1",
            moisture_threshold_low=0.2,
            moisture_threshold_high=0.45,
            schedule={"watering": "08:00"},
        )
        .build()
    )

    assert config.location.name == "Lab Site A"
    assert len(config.location.zones) == 1


def test_build_requires_name() -> None:
    with pytest.raises(ConfigurationError, match="Location name"):
        (
            LocationConfigBuilder()
            .add_zone("Bench 1", 0.2, 0.45)
            .build()
        )


def test_build_requires_zones() -> None:
    with pytest.raises(ConfigurationError, match="At least one zone"):
        LocationConfigBuilder().with_location_name("Lab Site A").build()


def test_build_rejects_invalid_thresholds() -> None:
    with pytest.raises(ConfigurationError, match="lower"):
        (
            LocationConfigBuilder()
            .with_location_name("Lab Site A")
            .add_zone("Bench 1", 0.6, 0.4)
            .build()
        )