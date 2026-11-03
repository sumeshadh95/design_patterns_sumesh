import { useEffect, useState } from "react";
import { useLocationZones, zoneLabel } from "../../hooks/useLocationZones";
import {
  createSensor,
  fetchSensorReadings,
  listSensors,
  readSensor,
  type DeviceDto,
  type ReadingDto,
  type SensorDto,
} from "../../services/api";
import SamplingControls from "./SamplingControls";

// Temporary: cards poll the latest stored reading so sampler rows show up
// without "Read now". Phase 12 replaces this poll with a WebSocket push.
const POLL_MS = 5000;

async function fetchLatestReadings(
  sensors: SensorDto[],
): Promise<Record<string, ReadingDto>> {
  const latestReadings = await Promise.all(
    sensors.map(async (sensor) => {
      const history = await fetchSensorReadings(sensor.id, 1);
      return [sensor.id, history[0]] as const;
    }),
  );

  return Object.fromEntries(
    latestReadings.filter(
      (entry): entry is readonly [string, ReadingDto] => entry[1] !== undefined,
    ),
  );
}

async function fetchSensorsWithLatest(): Promise<{
  sensors: SensorDto[];
  readings: Record<string, ReadingDto>;
}> {
  const sensors = await listSensors();

  return { sensors, readings: await fetchLatestReadings(sensors) };
}

type Props = {
  version: number;
};

export default function SensorList({ version }: Props) {
  const { configs } = useLocationZones(version);
  const [sensors, setSensors] = useState<SensorDto[]>([]);
  const [readings, setReadings] = useState<Record<string, ReadingDto>>({});
  const [loading, setLoading] = useState(true);
  const [readingDeviceId, setReadingDeviceId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSensors = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await fetchSensorsWithLatest();
      setSensors(data.sensors);
      setReadings(data.readings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    async function loadInitial() {
      try {
        const data = await fetchSensorsWithLatest();

        if (mounted) {
          setSensors(data.sensors);
          setReadings(data.readings);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadInitial();

    return () => {
      mounted = false;
    };
  }, [version]);

  useEffect(() => {
    if (sensors.length === 0) {
      return;
    }

    let mounted = true;

    const timer = window.setInterval(() => {
      fetchLatestReadings(sensors)
        .then((latest) => {
          if (mounted) {
            setReadings((current) => ({ ...current, ...latest }));
          }
        })
        .catch(() => {
          // Keep the last values; the next poll tries again.
        });
    }, POLL_MS);

    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, [sensors]);

  const handleCreate = async (type: "moisture" | "light") => {
    try {
      setError(null);
      await createSensor({ type, display_name: `${type} sensor` });
      await loadSensors();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create sensor");
    }
  };

  const handleReadNow = async (deviceId: string) => {
    try {
      setError(null);
      setReadingDeviceId(deviceId);

      const reading = await readSensor(deviceId);
      setReadings((current) => ({ ...current, [deviceId]: reading }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to read sensor");
    } finally {
      setReadingDeviceId(null);
    }
  };

  const handleSamplingSaved = (device: DeviceDto) => {
    setSensors((current) =>
      current.map((sensor) =>
        sensor.id === device.id
          ? {
              ...sensor,
              sampling_interval_seconds: device.sampling_interval_seconds,
              tracking_enabled: device.tracking_enabled,
            }
          : sensor,
      ),
    );
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Sensors</h3>
          <p className="text-sm text-slate-600">
            Latest stored readings. Cards refresh every few seconds (temporary
            poll until the Phase 12 WebSocket).
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
        {loading && <p className="text-slate-600">Loading sensors...</p>}

        {!loading && error && (
          <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        {!loading && !error && sensors.length === 0 && (
          <p className="text-sm text-slate-500">No sensors yet.</p>
        )}

        {!loading && sensors.length > 0 && (
          <div className="grid gap-3 md:grid-cols-2">
            {sensors.map((sensor) => {
              const reading = readings[sensor.id];
              const isReading = readingDeviceId === sensor.id;
              const zone = zoneLabel(configs, sensor.zone_id);

              return (
                <article
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

                  <p className="mt-1 text-xs text-slate-500">
                    {zone ?? "Unassigned"}
                  </p>

                  {reading ? (
                    <div className="mt-3 rounded-lg bg-white p-3 text-sm">
                      <p className="font-medium text-slate-900">
                        Latest: {reading.value} {reading.unit}
                      </p>
                      <span className="mt-2 inline-flex rounded-full bg-indigo-100 px-2 py-1 text-xs font-medium text-indigo-700">
                        {reading.source}
                      </span>
                      <p className="mt-2 text-xs text-slate-500">
                        {new Date(reading.recorded_at).toLocaleString()}
                      </p>
                    </div>
                  ) : (
                    <p className="mt-3 text-sm text-slate-500">
                      No stored readings yet.
                    </p>
                  )}

                  <SamplingControls
                    key={`${sensor.id}:${sensor.sampling_interval_seconds}:${sensor.tracking_enabled}`}
                    sensorId={sensor.id}
                    intervalSeconds={sensor.sampling_interval_seconds}
                    trackingEnabled={sensor.tracking_enabled}
                    onSaved={handleSamplingSaved}
                  />

                  <button
                    type="button"
                    disabled={isReading}
                    onClick={() => void handleReadNow(sensor.id)}
                    className="mt-4 rounded-lg bg-violet-600 px-3 py-2 text-sm font-medium text-white hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {isReading ? "Reading..." : "Read now"}
                  </button>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
