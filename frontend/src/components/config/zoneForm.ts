import type { ZoneBuildPayload, ZoneDto } from "../../services/api";

export type ZoneFields = {
  name: string;
  low: string;
  high: string;
  watering: string;
};

export const emptyZoneFields = (): ZoneFields => ({
  name: "",
  low: "0.2",
  high: "0.45",
  watering: "08:00",
});

export function zoneToFields(zone: ZoneDto): ZoneFields {
  return {
    name: zone.name,
    low: String(zone.moisture_threshold_low),
    high: String(zone.moisture_threshold_high),
    watering:
      typeof zone.schedule.watering === "string" ? zone.schedule.watering : "",
  };
}

// Same rules as the backend builder; the server still checks them again.
export function validateZoneFields(fields: ZoneFields): string | null {
  const low = Number(fields.low);
  const high = Number(fields.high);

  if (!fields.name.trim()) {
    return "Zone name is required.";
  }

  if (Number.isNaN(low) || Number.isNaN(high) || low < 0 || high > 1) {
    return "Thresholds must be numbers from 0 to 1.";
  }

  if (low >= high) {
    return "Low threshold must be lower than high.";
  }

  return null;
}

export function fieldsToPayload(fields: ZoneFields): ZoneBuildPayload {
  return {
    name: fields.name.trim(),
    moisture_threshold_low: Number(fields.low),
    moisture_threshold_high: Number(fields.high),
    schedule: fields.watering ? { watering: fields.watering } : {},
  };
}
