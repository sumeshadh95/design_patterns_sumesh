const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function errorMessage(response: Response, fallback: string): Promise<string> {
  const body = (await response.json().catch(() => null)) as {
    detail?: unknown;
  } | null;

  return typeof body?.detail === "string"
    ? body.detail
    : `${fallback}: ${response.status}`;
}

async function request<T>(
  path: string,
  fallback: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    throw new Error(await errorMessage(response, fallback));
  }

  return response.json() as Promise<T>;
}

async function requestNoContent(
  path: string,
  fallback: string,
  init: RequestInit,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    throw new Error(await errorMessage(response, fallback));
  }
}

function jsonBody(method: string, body: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export type HealthResponse = {
  status: string;
  db: "ok" | "fail";
};

export type SensorDto = {
  id: string;
  device_type: string;
  display_name: string | null;
  default_config: Record<string, unknown>;
  zone_id: string | null;
  location_id: string | null;
  sampling_interval_seconds: number;
  tracking_enabled: boolean;
};

export type SensorCreatePayload = {
  type: "moisture" | "light";
  display_name?: string | null;
};

export type DeviceRole = "sensor" | "actuator";
export type DeviceFamily = "simulation" | "edge";
export type ActuatorState =
  | "off"
  | "idle"
  | "running"
  | "error"
  | "maintenance";

export type DeviceDto = {
  id: string;
  device_type: string;
  role: DeviceRole;
  device_family: DeviceFamily | string;
  display_name: string;
  default_config: Record<string, unknown>;
  zone_id: string | null;
  location_id: string | null;
  sampling_interval_seconds: number;
  tracking_enabled: boolean;
  state: ActuatorState | null;
  allowed_commands: string[];
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

export function listSensors(): Promise<SensorDto[]> {
  return request("/api/sensors", "Failed to fetch sensors");
}

export function createSensor(payload: SensorCreatePayload): Promise<SensorDto> {
  return request(
    "/api/sensors",
    "Failed to create sensor",
    jsonBody("POST", payload),
  );
}

export function fetchDevices(
  filters: {
    family?: DeviceFamily;
    role?: DeviceRole;
  } = {},
): Promise<DeviceDto[]> {
  const params = new URLSearchParams();

  if (filters.family) params.set("family", filters.family);
  if (filters.role) params.set("role", filters.role);

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request(`/api/devices${suffix}`, "Failed to fetch devices");
}

export function provisionDeviceFamily(family: DeviceFamily): Promise<DeviceDto[]> {
  return request(
    `/api/devices/provision?family=${encodeURIComponent(family)}`,
    "Failed to provision family",
    { method: "POST" },
  );
}

export function assignDeviceZone(
  deviceId: string,
  zoneId: string | null,
): Promise<DeviceDto> {
  return request(
    `/api/devices/${deviceId}/zone`,
    "Failed to assign zone",
    jsonBody("PATCH", { zone_id: zoneId }),
  );
}

export function updateDeviceSampling(
  deviceId: string,
  samplingIntervalSeconds: number,
  trackingEnabled: boolean,
): Promise<DeviceDto> {
  return request(
    `/api/devices/${deviceId}/sampling`,
    "Failed to update sampling",
    jsonBody("PATCH", {
      sampling_interval_seconds: samplingIntervalSeconds,
      tracking_enabled: trackingEnabled,
    }),
  );
}

export function transitionDevice(
  deviceId: string,
  target: ActuatorState,
): Promise<DeviceDto> {
  return request(
    `/api/devices/${deviceId}/transition`,
    "Transition failed",
    jsonBody("POST", { target }),
  );
}

export type ZoneBuildPayload = {
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule?: Record<string, unknown>;
};

export type BuildLocationConfigPayload = {
  location_name: string;
  zones: ZoneBuildPayload[];
};

export type LocationDto = {
  id: string;
  name: string;
};

export type ZoneDto = {
  id: string;
  location_id: string;
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  schedule: Record<string, unknown>;
};

export type LocationConfigDto = {
  location: LocationDto;
  zones: ZoneDto[];
};

export function listLocations(): Promise<LocationDto[]> {
  return request("/api/locations", "Failed to fetch locations");
}

export function createLocationConfig(
  payload: BuildLocationConfigPayload,
): Promise<LocationConfigDto> {
  return request(
    "/api/locations/config",
    "Failed to create location config",
    jsonBody("POST", payload),
  );
}

export function fetchLocationConfig(locationId: string): Promise<LocationConfigDto> {
  return request(
    `/api/locations/${locationId}/config`,
    "Failed to fetch location config",
  );
}

export function deleteLocation(locationId: string): Promise<void> {
  return requestNoContent(`/api/locations/${locationId}`, "Failed to delete location", {
    method: "DELETE",
  });
}

export function addZone(locationId: string, zone: ZoneBuildPayload): Promise<ZoneDto> {
  return request(
    `/api/locations/${locationId}/zones`,
    "Failed to add zone",
    jsonBody("POST", zone),
  );
}

export function updateZone(
  locationId: string,
  zoneId: string,
  zone: ZoneBuildPayload,
): Promise<ZoneDto> {
  return request(
    `/api/locations/${locationId}/zones/${zoneId}`,
    "Failed to update zone",
    jsonBody("PATCH", zone),
  );
}

export function deleteZone(locationId: string, zoneId: string): Promise<void> {
  return requestNoContent(
    `/api/locations/${locationId}/zones/${zoneId}`,
    "Failed to delete zone",
    { method: "DELETE" },
  );
}

export function listZoneDevices(
  locationId: string,
  zoneId: string,
): Promise<DeviceDto[]> {
  return request(
    `/api/locations/${locationId}/zones/${zoneId}/devices`,
    "Failed to fetch zone devices",
  );
}

export type ReadingDto = {
  device_id: string;
  value: number;
  unit: string;
  source: "simulation" | "mqtt" | "vendor" | string;
  recorded_at: string;
};

export function readSensor(deviceId: string): Promise<ReadingDto> {
  return request(`/api/sensors/${deviceId}/read`, "Failed to read sensor", {
    method: "POST",
  });
}

export function fetchSensorReadings(
  deviceId: string,
  limit = 1,
): Promise<ReadingDto[]> {
  return request(
    `/api/sensors/${deviceId}/readings?limit=${limit}`,
    "Failed to fetch readings",
  );
}

export type StrategyKey = "conservative" | "aggressive";

export type ZoneRecommendationDto = {
  zone_id: string;
  zone_name: string;
  action: string;
  reason: string;
};

export type RecommendationDto = {
  location_id: string;
  strategy_key: string;
  action: string;
  reason: string;
  zones: ZoneRecommendationDto[];
};

export function saveStrategy(
  locationId: string,
  strategyKey: StrategyKey,
): Promise<{ location_id: string; strategy_key: string }> {
  return request(
    `/api/locations/${locationId}/automation`,
    "Save failed",
    jsonBody("PUT", { strategy_key: strategyKey }),
  );
}

export function evaluateAutomation(locationId: string): Promise<RecommendationDto> {
  return request(
    `/api/locations/${locationId}/automation/evaluate`,
    "Evaluate failed",
    { method: "POST" },
  );
}

export type LocationSummaryDto = {
  id: string;
  name: string;
};

export type DeviceCountsDto = {
  sensor: number;
  actuator: number;
};

export type OverviewDeviceDto = {
  id: string;
  device_type: string;
  role: DeviceRole;
  display_name: string;
};

export type ReadingSummaryDto = {
  device_id: string;
  value: number;
  unit: string;
  recorded_at: string;
  tracking_enabled: boolean;
  sampling_interval_seconds: number;
};

export type OverviewZoneDto = {
  id: string;
  name: string;
  moisture_threshold_low: number;
  moisture_threshold_high: number;
  devices: OverviewDeviceDto[];
  latest_readings: ReadingSummaryDto[];
};

export type RecommendationSummaryDto = {
  action: string;
  reason: string;
};

export type LocationOverviewDto = {
  location: LocationSummaryDto;
  device_counts: DeviceCountsDto;
  zones: OverviewZoneDto[];
  strategy_key: string | null;
  last_recommendation: RecommendationSummaryDto | null;
};

export function fetchOverview(locationId: string): Promise<LocationOverviewDto> {
  return request(
    `/api/locations/${locationId}/overview`,
    "Failed to fetch overview",
  );
}


export type ExecutionDto = {
  id: string;
  device_id: string;
  success: boolean;
  policy_applied: string[];
  message: string | null;
  created_at: string;
};

export function fetchExecutions(limit = 20): Promise<ExecutionDto[]> {
  return request(
    `/api/actuators/executions?limit=${limit}`,
    "Failed to fetch executions",
  );
}

