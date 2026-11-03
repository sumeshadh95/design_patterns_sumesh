import { useEffect, useState } from "react";
import { useLocationZones } from "../../hooks/useLocationZones";
import {
  addZone,
  createLocationConfig,
  deleteLocation,
  listZoneDevices,
  type DeviceDto,
  type LocationConfigDto,
} from "../../services/api";
import ZoneEditor from "./ZoneEditor";
import ZoneFieldsInputs from "./ZoneFieldsInputs";
import {
  emptyZoneFields,
  fieldsToPayload,
  validateZoneFields,
  type ZoneFields,
} from "./zoneForm";

type Props = {
  version: number;
  onChanged: () => void;
};

type ZoneDevices = {
  locationId: string;
  byZone: Record<string, DeviceDto[]>;
};

export default function LocationConfigWizard({ version, onChanged }: Props) {
  const { configs, error: loadError } = useLocationZones(version);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [zoneDevices, setZoneDevices] = useState<ZoneDevices | null>(null);

  const [locationName, setLocationName] = useState("");
  const [newZones, setNewZones] = useState<ZoneFields[]>([emptyZoneFields()]);
  const [extraZone, setExtraZone] = useState<ZoneFields>(emptyZoneFields());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const selected: LocationConfigDto | null =
    configs.find((config) => config.location.id === selectedId) ?? null;

  useEffect(() => {
    if (!selected) {
      return;
    }

    let mounted = true;
    const locationId = selected.location.id;
    const zones = selected.zones;

    async function loadZoneDevices() {
      try {
        const lists = await Promise.all(
          zones.map((zone) => listZoneDevices(locationId, zone.id)),
        );

        if (mounted) {
          setZoneDevices({
            locationId,
            byZone: Object.fromEntries(zones.map((zone, i) => [zone.id, lists[i]])),
          });
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load zone devices");
        }
      }
    }

    void loadZoneDevices();

    return () => {
      mounted = false;
    };
  }, [selected]);

  const devicesFor = (zoneId: string): DeviceDto[] =>
    zoneDevices && zoneDevices.locationId === selectedId
      ? zoneDevices.byZone[zoneId] ?? []
      : [];

  const run = async (action: () => Promise<void>, fallback: string) => {
    try {
      setBusy(true);
      setError(null);
      setSuccess(null);
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : fallback);
    } finally {
      setBusy(false);
    }
  };

  const handleCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!locationName.trim()) {
      setError("Location name is required.");
      return;
    }

    const problem = newZones.map(validateZoneFields).find(Boolean);
    if (problem) {
      setError(problem);
      return;
    }

    await run(async () => {
      const saved = await createLocationConfig({
        location_name: locationName.trim(),
        zones: newZones.map(fieldsToPayload),
      });
      setSelectedId(saved.location.id);
      setLocationName("");
      setNewZones([emptyZoneFields()]);
      setSuccess(`Saved location: ${saved.location.name}`);
      onChanged();
    }, "Failed to save location configuration.");
  };

  const handleDeleteLocation = async (id: string, name: string) => {
    if (!window.confirm(`Delete location "${name}" and all of its zones?`)) {
      return;
    }

    await run(async () => {
      await deleteLocation(id);
      if (selectedId === id) {
        setSelectedId(null);
      }
      setSuccess(`Deleted location: ${name}`);
      onChanged();
    }, "Failed to delete location.");
  };

  const handleAddZone = async () => {
    if (!selected) {
      return;
    }

    const problem = validateZoneFields(extraZone);
    if (problem) {
      setError(problem);
      return;
    }

    await run(async () => {
      await addZone(selected.location.id, fieldsToPayload(extraZone));
      setExtraZone(emptyZoneFields());
      setSuccess("Zone added.");
      onChanged();
    }, "Failed to add zone.");
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-xl font-semibold text-slate-900">Configuration</h3>
      <p className="mt-1 text-sm text-slate-600">
        Saved locations, their zones, and new locations built with the Builder.
      </p>

      <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
        <div>
          <h4 className="font-semibold text-slate-900">Saved locations</h4>

          {configs.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">No locations yet.</p>
          ) : (
            <ul className="mt-2 divide-y divide-slate-200 rounded-xl border border-slate-200">
              {configs.map(({ location }) => (
                <li
                  key={location.id}
                  className={`flex items-center justify-between gap-2 px-3 py-2 text-sm ${
                    location.id === selectedId ? "bg-emerald-50" : ""
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => setSelectedId(location.id)}
                    className="text-left font-medium text-slate-900 hover:underline"
                  >
                    {location.name}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void handleDeleteLocation(location.id, location.name)}
                    className="text-red-700 hover:underline disabled:opacity-50"
                  >
                    Delete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          {selected ? (
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-slate-900">{selected.location.name}</h4>
                <p className="break-all text-xs text-slate-500">
                  Location ID: {selected.location.id}
                </p>
              </div>

              {selected.zones.map((zone) => (
                <ZoneEditor
                  key={`${zone.id}:${zone.name}:${zone.moisture_threshold_low}:${zone.moisture_threshold_high}:${JSON.stringify(zone.schedule)}`}
                  zone={zone}
                  devices={devicesFor(zone.id)}
                  onChanged={onChanged}
                />
              ))}

              <div className="rounded-xl border border-dashed border-slate-300 p-4">
                <h5 className="mb-3 text-sm font-semibold text-slate-900">Add zone</h5>
                <ZoneFieldsInputs
                  fields={extraZone}
                  idPrefix="extra-zone"
                  onChange={setExtraZone}
                />
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void handleAddZone()}
                  className="mt-3 rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-50"
                >
                  Add zone
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">
              Select a location to see its zones, or create one.
            </p>
          )}
        </div>
      </div>

      <form
        className="mt-8 space-y-4 rounded-xl border border-slate-200 p-4"
        onSubmit={(event) => void handleCreate(event)}
      >
        <h4 className="font-semibold text-slate-900">New location</h4>

        <label className="block text-sm font-medium text-slate-700">
          Location name
          <input
            value={locationName}
            onChange={(event) => setLocationName(event.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
            placeholder="Lab Site A"
          />
        </label>

        {newZones.map((zone, index) => (
          <div key={index} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-slate-900">Zone {index + 1}</span>
              {newZones.length > 1 && (
                <button
                  type="button"
                  className="text-sm text-red-600"
                  onClick={() =>
                    setNewZones((current) => current.filter((_, i) => i !== index))
                  }
                >
                  Remove
                </button>
              )}
            </div>
            <ZoneFieldsInputs
              fields={zone}
              idPrefix={`new-zone-${index}`}
              onChange={(next) =>
                setNewZones((current) => current.map((z, i) => (i === index ? next : z)))
              }
            />
          </div>
        ))}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium"
            onClick={() => setNewZones((current) => [...current, emptyZoneFields()])}
          >
            Add zone
          </button>
          <button
            type="submit"
            disabled={busy}
            className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white disabled:opacity-70"
          >
            {busy ? "Saving..." : "Save location configuration"}
          </button>
        </div>
      </form>

      {(error || loadError) && (
        <p className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error ?? loadError}
        </p>
      )}

      {success && (
        <p className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
          {success}
        </p>
      )}
    </section>
  );
}
