import { useEffect, useState } from "react";
import {
  fetchOverview,
  type LocationOverviewDto,
} from "../../services/api";

const STORAGE_KEY = "greenhouse.overview.locationId";

function readSavedLocationId(): string {
  return window.localStorage.getItem(STORAGE_KEY) ?? "";
}

export default function OverviewPanel() {
  const [locationId, setLocationId] = useState(readSavedLocationId);
  const [overview, setOverview] = useState<LocationOverviewDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function load(id: string) {
    const trimmed = id.trim();

    if (!trimmed) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await fetchOverview(trimmed);
      setOverview(data);
      window.localStorage.setItem(STORAGE_KEY, trimmed);
    } catch (err) {
      setOverview(null);
      setError(err instanceof Error ? err.message : "Failed to load overview");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const saved = readSavedLocationId();

    if (!saved) {
      return;
    }

    let mounted = true;

    async function loadSaved() {
      try {
        const data = await fetchOverview(saved);

        if (mounted) {
          setOverview(data);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error ? err.message : "Failed to load overview",
          );
        }
      }
    }

    void loadSaved();

    return () => {
      mounted = false;
    };
  }, []);

  const recommendation = overview?.last_recommendation ?? null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Overview</h3>
          <p className="text-sm text-slate-600">
            One request to the location overview facade
          </p>
        </div>

        <button
          type="button"
          onClick={() => void load(locationId)}
          disabled={loading || !locationId.trim()}
          className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          {loading ? "Loading..." : overview ? "Refresh" : "Load"}
        </button>
      </div>

      <input
        className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        placeholder="location_id (uuid)"
        value={locationId}
        onChange={(event) => setLocationId(event.target.value)}
      />

      {error && (
        <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!error && !overview && (
        <p className="mt-3 text-sm text-slate-500">
          Enter a location id and load its overview.
        </p>
      )}

      {overview && (
        <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-medium uppercase text-slate-500">
              Location
            </p>
            <p className="mt-1 font-semibold text-slate-900">
              {overview.location.name}
            </p>
            <p className="mt-1 break-all text-xs text-slate-500">
              {overview.location.id}
            </p>
          </article>

          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-medium uppercase text-slate-500">
              Devices
            </p>
            <p className="mt-1 font-semibold text-slate-900">
              {overview.device_counts.sensor} sensors
            </p>
            <p className="text-sm text-slate-700">
              {overview.device_counts.actuator} actuators
            </p>
          </article>

          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-medium uppercase text-slate-500">
              Strategy
            </p>
            <p className="mt-1 font-semibold text-slate-900">
              {overview.strategy_key ?? "not set"}
            </p>
          </article>

          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-medium uppercase text-slate-500">
              Recommendation
            </p>
            {recommendation ? (
              <>
                <p className="mt-1 font-semibold text-slate-900">
                  {recommendation.action}
                </p>
                <p className="text-sm text-slate-700">
                  {recommendation.reason}
                </p>
              </>
            ) : (
              <p className="mt-1 text-sm text-slate-500">
                No recommendation yet.
              </p>
            )}
          </article>

          <article className="rounded-xl border border-slate-200 bg-slate-50 p-4 md:col-span-2 lg:col-span-4">
            <p className="text-xs font-medium uppercase text-slate-500">
              Latest readings
            </p>

            {overview.latest_readings.length === 0 ? (
              <p className="mt-1 text-sm text-slate-500">
                No stored readings yet.
              </p>
            ) : (
              <ul className="mt-2 divide-y divide-slate-200 text-sm">
                {overview.latest_readings.map((reading) => (
                  <li
                    key={reading.device_id}
                    className="flex flex-wrap items-center justify-between gap-2 py-2"
                  >
                    <span className="font-medium text-slate-900">
                      {reading.value} {reading.unit}
                    </span>
                    <span className="break-all text-xs text-slate-500">
                      {reading.device_id}
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(reading.recorded_at).toLocaleString()}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </div>
      )}
    </div>
  );
}
