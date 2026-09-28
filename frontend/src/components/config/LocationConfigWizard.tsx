import { useState } from "react";
import {
  createLocationConfig,
  type LocationConfigDto,
  type ZoneBuildPayload,
} from "../../services/api";

const emptyZone = (): ZoneBuildPayload => ({
  name: "",
  moisture_threshold_low: 0.2,
  moisture_threshold_high: 0.45,
  schedule: { watering: "08:00" },
});

export default function LocationConfigWizard() {
  const [locationName, setLocationName] = useState("");
  const [zones, setZones] = useState<ZoneBuildPayload[]>([emptyZone()]);
  const [result, setResult] = useState<LocationConfigDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function updateZone(
    index: number,
    field: keyof ZoneBuildPayload,
    value: string | number,
  ) {
    setZones((current) =>
      current.map((zone, zoneIndex) =>
        zoneIndex === index ? { ...zone, [field]: value } : zone,
      ),
    );
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!locationName.trim()) {
      setError("Location name is required.");
      return;
    }

    if (zones.some((zone) => !zone.name.trim())) {
      setError("Every zone needs a name.");
      return;
    }

    if (
      zones.some(
        (zone) =>
          zone.moisture_threshold_low < 0 ||
          zone.moisture_threshold_high > 1 ||
          zone.moisture_threshold_low >= zone.moisture_threshold_high,
      )
    ) {
      setError("Each zone needs thresholds from 0 to 1, with low below high.");
      return;
    }

    try {
      setSaving(true);
      setError(null);
      const saved = await createLocationConfig({
        location_name: locationName,
        zones,
      });
      setResult(saved);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Failed to save location configuration.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-xl font-semibold text-slate-900">
        Location configuration
      </h3>
      <p className="mt-1 text-sm text-slate-600">
        Build a location with one or more watering zones.
      </p>

      <form className="mt-6 space-y-5" onSubmit={submit}>
        <label className="block text-sm font-medium text-slate-700">
          Location name
          <input
            value={locationName}
            onChange={(event) => setLocationName(event.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            placeholder="Lab Site A"
          />
        </label>

        {zones.map((zone, index) => (
          <div
            key={index}
            className="rounded-xl border border-slate-200 bg-slate-50 p-4"
          >
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-slate-900">Zone {index + 1}</h4>
              {zones.length > 1 && (
                <button
                  type="button"
                  className="text-sm text-red-600"
                  onClick={() =>
                    setZones((current) =>
                      current.filter((_, zoneIndex) => zoneIndex !== index),
                    )
                  }
                >
                  Remove
                </button>
              )}
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <input
                value={zone.name}
                onChange={(event) => updateZone(index, "name", event.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Bench 1"
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={zone.moisture_threshold_low}
                onChange={(event) =>
                  updateZone(index, "moisture_threshold_low", Number(event.target.value))
                }
                className="rounded-lg border border-slate-300 px-3 py-2"
                aria-label={`Zone ${index + 1} low threshold`}
              />
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={zone.moisture_threshold_high}
                onChange={(event) =>
                  updateZone(index, "moisture_threshold_high", Number(event.target.value))
                }
                className="rounded-lg border border-slate-300 px-3 py-2"
                aria-label={`Zone ${index + 1} high threshold`}
              />
            </div>
          </div>
        ))}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium"
            onClick={() => setZones((current) => [...current, emptyZone()])}
          >
            Add zone
          </button>

          <button
            type="submit"
            disabled={saving}
            className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-70"
          >
            {saving ? "Saving..." : "Save location configuration"}
          </button>
        </div>
      </form>

      {error && (
        <p className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm">
          <p className="font-medium text-emerald-800">
            Saved location: {result.location.name}
          </p>
          <p className="mt-1 break-all text-emerald-700">
            Location ID: {result.location.id}
          </p>
          <ul className="mt-3 list-disc pl-5 text-emerald-800">
            {result.zones.map((zone) => (
              <li key={zone.id}>
                {zone.name}: {zone.moisture_threshold_low}–{zone.moisture_threshold_high}
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}