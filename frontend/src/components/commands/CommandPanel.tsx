import { useEffect, useState } from "react";
import {
  fetchCommands,
  fetchDevices,
  sendCommand,
  type CommandLogDto,
  type CommandStatus,
  type CommandType,
  type DeviceDto,
} from "../../services/api";
import ActuatorStateBadge from "../devices/ActuatorStateBadge";

const COMMANDS: CommandType[] = ["start_pump", "stop_pump", "set_light_level"];

const STATUS_STYLES: Record<CommandStatus, string> = {
  success: "bg-emerald-100 text-emerald-700",
  failed: "bg-amber-100 text-amber-700",
  rejected: "bg-red-100 text-red-700",
};

async function loadControls(): Promise<{
  actuators: DeviceDto[];
  history: CommandLogDto[];
}> {
  const [actuators, history] = await Promise.all([
    fetchDevices({ role: "actuator" }),
    fetchCommands(),
  ]);

  return { actuators, history };
}

type Props = {
  version: number;
  onChanged: () => void;
};

export default function CommandPanel({ version, onChanged }: Props) {
  const [actuators, setActuators] = useState<DeviceDto[]>([]);
  const [history, setHistory] = useState<CommandLogDto[]>([]);
  const [chosenId, setChosenId] = useState("");
  const [level, setLevel] = useState("1");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<CommandLogDto | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reloads the actuators and the history on load and after any change.
  useEffect(() => {
    let mounted = true;

    async function loadInitial() {
      try {
        const data = await loadControls();

        if (mounted) {
          setActuators(data.actuators);
          setHistory(data.history);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load controls");
        }
      }
    }

    void loadInitial();

    return () => {
      mounted = false;
    };
  }, [version]);

  // The chosen actuator, or the first one when nothing is chosen yet.
  const actuator =
    actuators.find((device) => device.id === chosenId) ?? actuators[0] ?? null;

  const refresh = async () => {
    try {
      setBusy(true);
      setError(null);

      const data = await loadControls();
      setActuators(data.actuators);
      setHistory(data.history);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load controls");
    } finally {
      setBusy(false);
    }
  };

  const handleCommand = async (commandType: CommandType) => {
    if (!actuator) {
      return;
    }

    try {
      setBusy(true);
      setError(null);

      const payload =
        commandType === "set_light_level" ? { level: Number(level) } : {};
      setResult(await sendCommand(commandType, actuator.id, payload));
      // Bumps the dashboard version: this panel reloads the actuators and
      // the history, and the Devices section shows the new state.
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Command failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Actuator controls</h3>
          <p className="text-sm text-slate-600">
            Each button sends a command. A button is disabled when the command is
            not in the actuator&apos;s allowed commands.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void refresh()}
          disabled={busy}
          className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          Refresh
        </button>
      </div>

      {error && (
        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {actuators.length === 0 ? (
        <p className="mt-4 text-sm text-slate-500">
          No actuators yet. Provision a device family under Devices.
        </p>
      ) : (
        <div className="mt-4 space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label="Actuator"
              value={actuator?.id ?? ""}
              onChange={(event) => setChosenId(event.target.value)}
              className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
            >
              {actuators.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.display_name} · {device.state ?? "idle"} · {device.id.slice(0, 8)}
                </option>
              ))}
            </select>

            {actuator?.state && (
              <ActuatorStateBadge
                state={actuator.state}
                allowedCommands={actuator.allowed_commands}
              />
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {COMMANDS.map((commandType) => (
              <button
                key={commandType}
                type="button"
                onClick={() => void handleCommand(commandType)}
                disabled={
                  busy || !actuator?.allowed_commands.includes(commandType)
                }
                className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500"
              >
                {commandType}
              </button>
            ))}

            <label className="flex items-center gap-2 text-sm text-slate-700">
              Level
              <input
                type="number"
                value={level}
                onChange={(event) => setLevel(event.target.value)}
                className="w-20 rounded-lg border border-slate-300 px-2 py-1"
              />
            </label>
          </div>

          {result && (
            <p className="text-sm text-slate-700">
              Last command: <span className="font-medium">{result.command_type}</span>{" "}
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[result.status]}`}
              >
                {result.status}
              </span>
              {result.error_message && ` ${result.error_message}`}
            </p>
          )}
        </div>
      )}

      <h4 className="mt-6 font-semibold text-slate-900">Command history</h4>

      {history.length === 0 ? (
        <p className="mt-2 text-sm text-slate-500">No commands yet.</p>
      ) : (
        <div className="mt-2 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2 pr-4 font-medium">Time</th>
                <th className="py-2 pr-4 font-medium">Command</th>
                <th className="py-2 pr-4 font-medium">Device</th>
                <th className="py-2 pr-4 font-medium">Payload</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 font-medium">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.map((row) => (
                <tr key={row.id}>
                  <td className="py-2 pr-4 whitespace-nowrap text-slate-700">
                    {new Date(row.created_at).toLocaleString()}
                  </td>
                  <td className="py-2 pr-4 text-slate-900">{row.command_type}</td>
                  <td
                    className="py-2 pr-4 font-mono text-xs text-slate-700"
                    title={row.device_id}
                  >
                    {row.device_id.slice(0, 8)}
                  </td>
                  <td className="py-2 pr-4 font-mono text-xs text-slate-700">
                    {JSON.stringify(row.payload)}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[row.status]}`}
                    >
                      {row.status}
                    </span>
                  </td>
                  <td className="py-2 text-slate-700">{row.error_message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
