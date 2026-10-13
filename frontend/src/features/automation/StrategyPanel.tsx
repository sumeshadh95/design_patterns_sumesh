import { useState } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type EvaluateResult = {
  location_id: string;
  strategy_key: string;
  action: string;
  reason: string;
};

export default function StrategyPanel() {
  const [locationId, setLocationId] = useState("");
  const [strategyKey, setStrategyKey] = useState("conservative");
  const [result, setResult] = useState<EvaluateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function save() {
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/locations/${locationId}/automation`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            strategy_key: strategyKey,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(
          (await response.text()) || `Save failed ${response.status}`,
        );
      }

      setSuccess("Strategy saved");
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Save failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function evaluate() {
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/locations/${locationId}/automation/evaluate`,
        {
          method: "POST",
        },
      );

      if (!response.ok) {
        throw new Error(
          (await response.text()) ||
            `Evaluate failed ${response.status}`,
        );
      }

      const data = (await response.json()) as EvaluateResult;
      setResult(data);
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Evaluate failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-xl font-semibold text-slate-900">
        Automation Strategy
      </h3>

      <p className="text-sm text-slate-600">
        Save strategy key then evaluate from DB readings
      </p>

      <input
        className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        placeholder="location_id (uuid)"
        value={locationId}
        onChange={(event) => setLocationId(event.target.value)}
      />

      <div className="mt-3 flex gap-2">
        <select
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={strategyKey}
          onChange={(event) => setStrategyKey(event.target.value)}
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

      {result && (
        <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">
          <p className="font-medium text-slate-900">
            action: {result.action}
          </p>
          <p className="text-slate-700">
            reason: {result.reason}
          </p>
          <p className="text-xs text-slate-500">
            {result.strategy_key}
          </p>
        </div>
      )}
    </div>
  );
}