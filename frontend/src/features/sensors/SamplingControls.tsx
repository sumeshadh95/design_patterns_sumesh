import { useState } from "react";
import { updateDeviceSampling, type DeviceDto } from "../../services/api";

type Props = {
  sensorId: string;
  intervalSeconds: number;
  trackingEnabled: boolean;
  onSaved: (device: DeviceDto) => void;
};

export default function SamplingControls({
  sensorId,
  intervalSeconds,
  trackingEnabled,
  onSaved,
}: Props) {
  const [interval, setIntervalValue] = useState(String(intervalSeconds));
  const [tracking, setTracking] = useState(trackingEnabled);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  const handleSave = async () => {
    const seconds = Number(interval);

    if (!Number.isInteger(seconds) || seconds < 5) {
      setMessage({ ok: false, text: "Interval must be a whole number of at least 5 seconds." });
      return;
    }

    try {
      setBusy(true);
      setMessage(null);
      onSaved(await updateDeviceSampling(sensorId, seconds, tracking));
      setMessage({ ok: true, text: "Sampling saved" });
    } catch (err) {
      setMessage({
        ok: false,
        text: err instanceof Error ? err.message : "Failed to save sampling",
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-3 rounded-lg bg-white p-3 text-sm">
      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-slate-700">
          Every
          <input
            type="number"
            min="5"
            step="1"
            value={interval}
            onChange={(event) => setIntervalValue(event.target.value)}
            className="w-20 rounded-lg border border-slate-300 px-2 py-1"
          />
          s
        </label>

        <label className="flex items-center gap-2 text-slate-700">
          <input
            type="checkbox"
            checked={tracking}
            onChange={(event) => setTracking(event.target.checked)}
          />
          Tracking
        </label>

        <button
          type="button"
          disabled={busy}
          onClick={() => void handleSave()}
          className="rounded-lg bg-slate-800 px-3 py-1 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          Save
        </button>
      </div>

      {message && (
        <p className={`mt-2 text-xs ${message.ok ? "text-emerald-700" : "text-red-700"}`}>
          {message.text}
        </p>
      )}
    </div>
  );
}
