import { useEffect, useState } from "react";
import { createSensor, listSensors, type SensorDto } from "../../services/api";

export default function SensorList() {
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSensors = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listSensors();
      setSensors(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadSensors();
  }, []);

  const handleCreate = async (type: "moisture" | "light") => {
    try {
      setError(null);
      await createSensor({ type, display_name: `${type} sensor` });
      await loadSensors();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create sensor");
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Sensors</h3>
          <p className="text-sm text-slate-600">
            Manage moisture and light sensors
          </p>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void handleCreate("moisture")}
            className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
          >
            Add moisture
          </button>

          <button
            type="button"
            onClick={() => void handleCreate("light")}
            className="rounded-lg bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700"
          >
            Add light
          </button>
        </div>
      </div>

      <div className="mt-6">
        {loading && <p className="text-slate-600">Loading sensors…</p>}

        {!loading && error && (
          <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        {!loading && !error && sensors.length === 0 && (
          <p className="text-sm text-slate-500">No sensors yet.</p>
        )}

        {!loading && !error && sensors.length > 0 && (
          <div className="grid gap-3 md:grid-cols-2">
            {sensors.map((sensor) => (
              <div
                key={sensor.id}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-semibold text-slate-900">
                    {sensor.display_name ?? sensor.device_type}
                  </h4>
                  <span className="rounded-full bg-slate-200 px-2 py-1 text-xs font-medium text-slate-700">
                    {sensor.device_type}
                  </span>
                </div>

                <ul className="mt-3 space-y-1 text-sm text-slate-600">
                  <li>ID: {sensor.id}</li>
                  <li>Config: {JSON.stringify(sensor.default_config)}</li>
                </ul>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}