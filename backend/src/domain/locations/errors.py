class ConfigurationError(ValueError):
    pass


class LocationNotFoundError(LookupError):
    pass


class ZoneNotFoundError(LookupError):
    pass


class DeviceNotFoundError(LookupError):
    pass
