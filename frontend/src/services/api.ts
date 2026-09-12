const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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

export async function fetchHealth(): Promise<{ status: string; db: "ok" | "fail" }> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health request failed: ${response.status}`);
  }

  return response.json() as Promise<{ status: string; db: "ok" | "fail" }>;
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
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to create sensor: ${response.status}`);
  }

  return response.json() as Promise<SensorDto>;
}