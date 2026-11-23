import { useEffect, useState } from "react";
import { useLocationZones, zoneLabel } from "../../hooks/useLocationZones";
import { fetchAlerts, type AlertDto, type AlertSeverity } from "../../services/api";

// Polls the alerts API. Phase 12 adds the WebSocket (services/realtime.ts).
const POLL_MS = 5000;

const SEVERITY_STYLES: Record<AlertSeverity, string> = {
  info: "bg-sky-100 text-sky-700",
  warning: "bg-amber-100 text-amber-700",
  critical: "bg-red-100 text-red-700",
};

type Props = {
  version: number;
};

export default function EventFeed({ version }: Props) {
  const { configs } = useLocationZones(version);
  const [locationId, setLocationId] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [alerts, setAlerts] = useState<AlertDto[]>([]);
  const [error, setError] = useState<string | null>(null);

  const zones =
    configs.find((config) => config.location.id === locationId)?.zones ?? [];

  // Loads now, then every 5 seconds, for the chosen location and zone.
  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        const data = await fetchAlerts({
          locationId: locationId || undefined,
          zoneId: zoneId || undefined,
        });

        if (mounted) {
          setAlerts(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load alerts");
        }
      }
    }

    void load();
    const timer = window.setInterval(() => void load(), POLL_MS);

    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [locationId, zoneId]);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Event feed</h3>
          <p className="text-sm text-slate-600">
            Active alerts from the alerts table. Refreshes every 5 seconds.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            aria-label="Location filter"
            value={locationId}
            onChange={(event) => {
              setLocationId(event.target.value);
              setZoneId("");
            }}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="">All locations</option>
            {configs.map(({ location }) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>

          <select
            aria-label="Zone filter"
            value={zoneId}
            onChange={(event) => setZoneId(event.target.value)}
            disabled={!locationId}
            className="rounded-lg border border-slate-300 px-3 py-2 text-sm disabled:opacity-50"
          >
            <option value="">All zones</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!error && alerts.length === 0 && (
        <p className="mt-4 text-sm text-slate-500">No alerts.</p>
      )}

      {alerts.length > 0 && (
        <ul className="mt-4 divide-y divide-slate-100">
          {alerts.map((alert) => (
            <li key={alert.id} className="flex flex-wrap items-start gap-3 py-3">
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[alert.severity]}`}
              >
                {alert.severity}
              </span>

              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-slate-900">{alert.message}</p>
                <p className="text-xs text-slate-500">
                  {alert.event_type} · {zoneLabel(configs, alert.zone_id) ?? "Unassigned"}
                  {alert.device_id && ` · device ${alert.device_id.slice(0, 8)}`}
                </p>
              </div>

              <span className="whitespace-nowrap text-xs text-slate-500">
                {new Date(alert.created_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
