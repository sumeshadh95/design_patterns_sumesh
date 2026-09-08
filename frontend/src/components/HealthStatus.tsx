import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "../services/api";

type HealthState =
  | { kind: "checking" }
  | { kind: "healthy"; data: HealthResponse }
  | { kind: "degraded"; data: HealthResponse }
  | { kind: "error" };

export default function HealthStatus() {
  const [state, setState] = useState<HealthState>({
    kind: "checking",
  });

  useEffect(() => {
    let mounted = true;

    async function loadHealth() {
      try {
        const data = await fetchHealth();

        if (!mounted) {
          return;
        }

        if (data.status === "ok" && data.db === "ok") {
          setState({ kind: "healthy", data });
        } else {
          setState({ kind: "degraded", data });
        }
      } catch {
        if (mounted) {
          setState({ kind: "error" });
        }
      }
    }

    loadHealth();

    const interval = window.setInterval(loadHealth, 10000);

    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  if (state.kind === "checking") {
    return (
      <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-sm text-amber-700">
        Checking…
      </span>
    );
  }

  if (state.kind === "error") {
    return (
      <span className="rounded-full border border-red-300 bg-red-50 px-3 py-1 text-sm text-red-700">
        API: unreachable
      </span>
    );
  }

  if (state.kind === "degraded") {
    return (
      <span className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-sm text-amber-700">
        API: {state.data.status} · DB: {state.data.db}
      </span>
    );
  }

  return (
    <span className="rounded-full border border-emerald-300 bg-emerald-50 px-3 py-1 text-sm text-emerald-700">
      API: ok · DB: ok
    </span>
  );
}