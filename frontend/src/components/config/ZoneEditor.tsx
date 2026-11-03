import { useState } from "react";
import {
  deleteZone,
  updateZone,
  type DeviceDto,
  type ZoneDto,
} from "../../services/api";
import ZoneFieldsInputs from "./ZoneFieldsInputs";
import {
  fieldsToPayload,
  validateZoneFields,
  zoneToFields,
  type ZoneFields,
} from "./zoneForm";

type Props = {
  zone: ZoneDto;
  devices: DeviceDto[];
  onChanged: () => void;
};

export default function ZoneEditor({ zone, devices, onChanged }: Props) {
  const [fields, setFields] = useState<ZoneFields>(() => zoneToFields(zone));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    const problem = validateZoneFields(fields);

    if (problem) {
      setError(problem);
      return;
    }

    try {
      setBusy(true);
      setError(null);
      await updateZone(zone.location_id, zone.id, fieldsToPayload(fields));
      setSaved(true);
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update zone");
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Delete zone "${zone.name}"? Its devices become unassigned.`)) {
      return;
    }

    try {
      setBusy(true);
      setError(null);
      await deleteZone(zone.location_id, zone.id);
      onChanged();
    } catch (err) {
      // For example the API rejects deleting the last zone.
      setError(err instanceof Error ? err.message : "Failed to delete zone");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <ZoneFieldsInputs
        fields={fields}
        idPrefix={`zone-${zone.id}`}
        onChange={(next) => {
          setFields(next);
          setSaved(false);
        }}
      />

      <p className="mt-3 text-sm text-slate-700">
        Devices:{" "}
        {devices.length > 0 ? (
          <span className="font-medium text-slate-900">
            {devices.map((device) => device.display_name).join(", ")}
          </span>
        ) : (
          <span className="text-slate-500">none assigned</span>
        )}
      </p>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void handleSave()}
          className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          Save zone
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => void handleDelete()}
          className="rounded-lg border border-red-200 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
        >
          Delete zone
        </button>
        {saved && <span className="text-sm text-emerald-700">Saved</span>}
      </div>

      {error && (
        <p className="mt-2 rounded border border-red-200 bg-red-50 p-2 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
