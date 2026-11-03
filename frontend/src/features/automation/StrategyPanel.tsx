import { useState } from "react";
import { useLocationZones } from "../../hooks/useLocationZones";
import {
  evaluateAutomation,
  saveStrategy,
  type RecommendationDto,
  type StrategyKey,
} from "../../services/api";

type Props = {
  version: number;
  onChanged: () => void;
};

export default function StrategyPanel({ version, onChanged }: Props) {
  const { configs } = useLocationZones(version);
  const [chosenId, setChosenId] = useState("");
  const [strategyKey, setStrategyKey] = useState<StrategyKey>("conservative");
  const [result, setResult] = useState<RecommendationDto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const locationId =
    configs.find((config) => config.location.id === chosenId)?.location.id ??
    configs[0]?.location.id ??
    "";

  const run = async (action: () => Promise<void>, fallback: string) => {
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : fallback);
    } finally {
      setLoading(false);
    }
  };

  const save = () =>
    run(async () => {
      await saveStrategy(locationId, strategyKey);
      setSuccess(`Strategy saved: ${strategyKey}`);
      onChanged();
    }, "Save failed");

  const evaluate = () =>
    run(async () => {
      setResult(await evaluateAutomation(locationId));
    }, "Evaluate failed");

  const shown = result && result.location_id === locationId ? result : null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-xl font-semibold text-slate-900">Automation Strategy</h3>
      <p className="text-sm text-slate-600">
        Save a strategy key, then evaluate each zone from its own sensors
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        <select
          aria-label="Location"
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

        <select
          aria-label="Strategy"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={strategyKey}
          onChange={(event) => setStrategyKey(event.target.value as StrategyKey)}
        >
          <option value="conservative">conservative</option>
          <option value="aggressive">aggressive</option>
        </select>

        <button
          type="button"
          onClick={() => void save()}
          disabled={loading || !locationId}
          className="rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          Save
        </button>

        <button
          type="button"
          onClick={() => void evaluate()}
          disabled={loading || !locationId}
          className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          Evaluate
        </button>
      </div>

      {error && (
        <p className="mt-3 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {success && (
        <p className="mt-3 rounded border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
          {success}
        </p>
      )}

      {shown && (
        <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">
          <p className="font-medium text-slate-900">action: {shown.action}</p>
          <p className="text-slate-700">reason: {shown.reason}</p>
          <p className="text-xs text-slate-500">strategy: {shown.strategy_key}</p>

          <ul className="mt-2 space-y-1 border-t border-slate-200 pt-2">
            {shown.zones.map((zone) => (
              <li key={zone.zone_id} className="text-slate-700">
                <span className="font-medium text-slate-900">{zone.zone_name}</span>
                {": "}
                {zone.action}, {zone.reason}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
