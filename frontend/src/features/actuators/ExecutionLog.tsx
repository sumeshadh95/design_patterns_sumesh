import { useEffect, useState } from "react";
import { fetchExecutions, type ExecutionDto } from "../../services/api";

export default function ExecutionLog() {
  const [executions, setExecutions] = useState<ExecutionDto[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function loadExecutions() {
      try {
        const data = await fetchExecutions();

        if (mounted) {
          setExecutions(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load executions");
        }
      }
    }

    void loadExecutions();

    return () => {
      mounted = false;
    };
  }, []);

  const refresh = async () => {
    try {
      setLoading(true);
      setError(null);
      setExecutions(await fetchExecutions());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load executions");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Execution log</h3>
          <p className="text-sm text-slate-600">
            Recent actuator attempts through the decorated port
          </p>
        </div>

        <button
          type="button"
          onClick={() => void refresh()}
          disabled={loading}
          className="rounded-lg bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>
      <p className="mt-3 rounded-lg bg-slate-50 p-3 text-sm text-slate-600">
        Any command succeeds until the actuator has been <strong>running</strong> for
        30 minutes. A success row has an empty message and the policy{" "}
        <code>logging</code>. A blocked row shows <em>Max run time exceeded</em> with
        the policies <code>maxRunTime</code> and <code>logging</code>.
      </p>

      {error && (
        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!error && executions.length === 0 && (
        <p className="mt-4 text-sm text-slate-500">No actuator executions yet.</p>
      )}

      {executions.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="py-2 pr-4 font-medium">Time</th>
                <th className="py-2 pr-4 font-medium">Device</th>
                <th className="py-2 pr-4 font-medium">Result</th>
                <th className="py-2 pr-4 font-medium">Policies</th>
                <th className="py-2 font-medium">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {executions.map((execution) => (
                <tr key={execution.id}>
                  <td className="py-2 pr-4 whitespace-nowrap text-slate-700">
                    {new Date(execution.created_at).toLocaleString()}
                  </td>
                  <td
                    className="py-2 pr-4 font-mono text-xs text-slate-700"
                    title={execution.device_id}
                  >
                    {execution.device_id.slice(0, 8)}
                  </td>
                  <td className="py-2 pr-4">
                    <span
                      className={
                        execution.success
                          ? "rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700"
                          : "rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700"
                      }
                    >
                      {execution.success ? "success" : "failed"}
                    </span>
                  </td>
                  <td className="py-2 pr-4 text-slate-700">
                    {execution.policy_applied.join(", ")}
                  </td>
                  <td className="py-2 text-slate-700">{execution.message ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
