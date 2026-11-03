import { useState } from "react";
import { zoneLabel } from "../../hooks/useLocationZones";
import {
  assignDeviceZone,
  type DeviceDto,
  type LocationConfigDto,
} from "../../services/api";

type Props = {
  deviceId: string;
  zoneId: string | null;
  configs: LocationConfigDto[];
  onAssigned: (device: DeviceDto) => void;
};

export default function ZonePicker({ deviceId, zoneId, configs, onAssigned }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // A zone that no longer exists (for example after a delete) shows as unassigned.
  const current = zoneLabel(configs, zoneId) ? zoneId ?? "" : "";

  const handleChange = async (value: string) => {
    try {
      setBusy(true);
      setError(null);
      onAssigned(await assignDeviceZone(deviceId, value || null));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to assign zone");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-3 text-sm">
      <label className="flex flex-wrap items-center gap-2 text-slate-700">
        Zone
        <select
          aria-label="Assigned zone"
          value={current}
          disabled={busy}
          onChange={(event) => void handleChange(event.target.value)}
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-2 py-1 text-sm"
        >
          <option value="">Unassigned</option>
          {configs.map(({ location, zones }) => (
            <optgroup key={location.id} label={location.name}>
              {zones.map((zone) => (
                <option key={zone.id} value={zone.id}>
                  {location.name} — {zone.name}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>

      {error && <p className="mt-1 text-xs text-red-700">{error}</p>}
    </div>
  );
}
