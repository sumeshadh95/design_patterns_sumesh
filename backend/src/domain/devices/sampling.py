from __future__ import annotations

from domain.devices.entity import MIN_SAMPLING_INTERVAL_SECONDS


class SamplingConfigError(ValueError):
    pass


def validate_sampling_interval(seconds: int) -> None:
    if seconds < MIN_SAMPLING_INTERVAL_SECONDS:
        raise SamplingConfigError(
            "sampling_interval_seconds must be at least "
            f"{MIN_SAMPLING_INTERVAL_SECONDS}."
        )
