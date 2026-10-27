import { useState } from "react";
import {
  transitionDevice,
  type ActuatorState,
  type DeviceDto,
} from "../../services/api";

const STATES: ActuatorState[] = [
  "off",
  "idle",
  "running",
  "error",
  "maintenance",
];

type Props = {
  device: DeviceDto;
  onChanged: (device: DeviceDto) => void;
};

export default function ActuatorStateControl({ device, onChanged }: Props) {
  const [target, setTarget] = useState<ActuatorState>("running");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // The UI offers every other state; the backend decides which moves are legal.
  const options = STATES.filter((state) => state !== device.state);
  const selected = options.includes(target) ? target : options[0];

  const handleApply = async () => {
    try {
      setBusy(true);
      setError(null);
      onChanged(await transitionDevice(device.id, selected));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Transition failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mt-3 rounded-lg bg-white p-3 text-sm">
      <p className="text-slate-700">
        Allowed commands:{" "}
        <span className="font-medium text-slate-900">
          {device.allowed_commands.length > 0
            ? device.allowed_commands.join(", ")
            : "none"}
        </span>
      </p>

      <div className="mt-2 flex items-center gap-2">
        <select
          aria-label="Target state"
          className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
          value={selected}
          onChange={(event) => setTarget(event.target.value as ActuatorState)}
        >
          {options.map((state) => (
            <option key={state} value={state}>
              {state}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={() => void handleApply()}
          disabled={busy}
          className="rounded-lg bg-slate-800 px-3 py-1 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          {busy ? "Applying..." : "Set state"}
        </button>
      </div>

      {error && (
        <p className="mt-2 rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
