const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
  db: "ok" | "fail";
};

export type SensorDto = {
  id: string;
  device_type: string;
  display_name: string | null;
  default_config: Record<string, unknown>;
};

export type SensorCreatePayload = {
  type: "moisture" | "light";
  display_name?: string | null;
};

export type DeviceRole = "sensor" | "actuator";
export type DeviceFamily = "simulation" | "edge";

export type DeviceDto = {
  id: string;
  device_type: string;
  role: DeviceRole;
  device_family: DeviceFamily | string;
  display_name: string;
  default_config: Record<string, unknown>;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

export async function listSensors(): Promise<SensorDto[]> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`);

  if (!response.ok) {
    throw new Error(`Failed to fetch sensors: ${response.status}`);
  }

  return response.json() as Promise<SensorDto[]>;
}

export async function createSensor(
  payload: SensorCreatePayload,
): Promise<SensorDto> {
  const response = await fetch(`${API_BASE_URL}/api/sensors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to create sensor: ${response.status}`);
  }

  return response.json() as Promise<SensorDto>;
}

export async function fetchDevices(
  filters: {
    family?: DeviceFamily;
    role?: DeviceRole;
  } = {},
): Promise<DeviceDto[]> {
  const params = new URLSearchParams();

  if (filters.family) params.set("family", filters.family);
  if (filters.role) params.set("role", filters.role);

  const suffix = params.toString() ? `?${params.toString()}` : "";
  const response = await fetch(`${API_BASE_URL}/api/devices${suffix}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch devices: ${response.status}`);
  }

  return response.json() as Promise<DeviceDto[]>;
}

export async function provisionDeviceFamily(
  family: DeviceFamily,
): Promise<DeviceDto[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/devices/provision?family=${encodeURIComponent(family)}`,
    { method: "POST" },
  );

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to provision family: ${response.status}`);
  }

  return response.json() as Promise<DeviceDto[]>;
}