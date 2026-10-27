import type { ActuatorState } from "../../services/api";

const STATE_STYLES: Record<ActuatorState, string> = {
  off: "bg-slate-700 text-white",
  idle: "bg-slate-200 text-slate-700",
  running: "bg-emerald-100 text-emerald-700",
  error: "bg-red-100 text-red-700",
  maintenance: "bg-amber-100 text-amber-700",
};

type Props = {
  state: ActuatorState;
  allowedCommands: string[];
};

export default function ActuatorStateBadge({ state, allowedCommands }: Props) {
  const tooltip =
    allowedCommands.length > 0
      ? `Allowed commands: ${allowedCommands.join(", ")}`
      : "No commands are allowed in this state";

  return (
    <span
      title={tooltip}
      className={`rounded-full px-2 py-1 text-xs font-medium ${STATE_STYLES[state]}`}
    >
      {state}
    </span>
  );
}
