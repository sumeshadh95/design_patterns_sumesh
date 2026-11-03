import { useEffect, useState } from "react";
import { useLocationZones } from "../../hooks/useLocationZones";
import { fetchOverview, type LocationOverviewDto } from "../../services/api";

type Props = {
  version: number;
};

export default function OverviewPanel({ version }: Props) {
  const { configs } = useLocationZones(version);
  const [chosenId, setChosenId] = useState("");
  const [overview, setOverview] = useState<LocationOverviewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // The chosen location, or the first saved one when nothing is chosen yet.
  const locationId =
    configs.find((config) => config.location.id === chosenId)?.location.id ??
    configs[0]?.location.id ??
    "";

  // One overview fetch per selected location.
  useEffect(() => {
    if (!locationId) {
      return;
    }

    let mounted = true;

    async function loadSelected() {
      try {
        const data = await fetchOverview(locationId);

        if (mounted) {
          setOverview(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setOverview(null);
          setError(err instanceof Error ? err.message : "Failed to load overview");
        }
      }
    }

    void loadSelected();

    return () => {
      mounted = false;
    };
  }, [locationId]);

  // Refresh repeats the same single fetch.
  const refresh = async () => {
    if (!locationId) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setOverview(await fetchOverview(locationId));
    } catch (err) {
      setOverview(null);
      setError(err instanceof Error ? err.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  };

  const shown = overview && overview.location.id === locationId ? overview : null;
  const recommendation = shown?.last_recommendation ?? null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Overview</h3>
          <p className="text-sm text-slate-600">
            One request to the location overview facade
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-700" htmlFor="overview-location">
            Location
          </label>
          <select
            id="overview-location"
            value={locationId}
            onChange={(event) => setChosenId(event.target.value)}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            {configs.length === 0 && <option value="">No locations</option>}
            {configs.map(({ location }) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => void refresh()}
            disabled={loading || !locationId}
            className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!locationId && (
        <p className="mt-4 text-sm text-slate-500">
          Create a location under Configuration to see its overview.
        </p>
      )}

      {shown && (
        <>
          <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
            <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Assigned sensors</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">
                {shown.device_counts.sensor}
              </p>
            </article>

            <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Assigned actuators</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">
                {shown.device_counts.actuator}
              </p>
            </article>

            <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Strategy</p>
              <p className="mt-1 font-semibold text-slate-900">
                {shown.strategy_key ?? "No strategy saved"}
              </p>
            </article>

            <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase text-slate-500">Recommendation</p>
              {recommendation ? (
                <>
                  <p className="mt-1 font-semibold text-slate-900">{recommendation.action}</p>
                  <p className="text-sm text-slate-700">{recommendation.reason}</p>
                </>
              ) : (
                <p className="mt-1 text-sm text-slate-500">
                  Save a strategy to get a recommendation.
                </p>
              )}
            </article>
          </div>

          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {shown.zones.map((zone) => (
              <article
                key={zone.id}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-semibold text-slate-900">{zone.name}</h4>
                  <span className="text-xs text-slate-500">
                    moisture {zone.moisture_threshold_low}–{zone.moisture_threshold_high}
                  </span>
                </div>

                {zone.devices.length === 0 ? (
                  <p className="mt-2 text-sm text-slate-500">
                    No devices assigned to this zone.
                  </p>
                ) : (
                  <ul className="mt-2 space-y-2 text-sm">
                    {zone.devices.map((device) => {
                      const reading = zone.latest_readings.find(
                        (row) => row.device_id === device.id,
                      );

                      return (
                        <li key={device.id}>
                          <p className="font-medium text-slate-900">{device.display_name}</p>
                          <p className="text-xs text-slate-500">
                            {device.role} · {device.device_type}
                          </p>
                          <p className="text-xs text-slate-700">
                            {reading
                              ? `${reading.value} ${reading.unit} · tracking ${
                                  reading.tracking_enabled ? "on" : "off"
                                } · every ${reading.sampling_interval_seconds}s · ${new Date(
                                  reading.recorded_at,
                                ).toLocaleTimeString()}`
                              : "No reading yet"}
                          </p>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </article>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
