import { useEffect, useState } from "react";
import {
  fetchLocationConfig,
  listLocations,
  type LocationConfigDto,
} from "../services/api";

/**
 * Every saved location with its zones. Reloads whenever `version` changes,
 * so a location or zone edit elsewhere on the dashboard shows up here.
 */
export function useLocationZones(version: number) {
  const [configs, setConfigs] = useState<LocationConfigDto[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const locations = await listLocations();
        const loaded = await Promise.all(
          locations.map((location) => fetchLocationConfig(location.id)),
        );

        if (mounted) {
          setConfigs(loaded);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load zones");
        }
      }
    }

    void load();

    return () => {
      mounted = false;
    };
  }, [version]);

  return { configs, error };
}

export function zoneLabel(
  configs: LocationConfigDto[],
  zoneId: string | null,
): string | null {
  for (const { location, zones } of configs) {
    const zone = zones.find((candidate) => candidate.id === zoneId);
    if (zone) {
      return `${location.name} — ${zone.name}`;
    }
  }

  return null;
}
