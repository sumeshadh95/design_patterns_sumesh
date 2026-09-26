import DeviceList from "../components/devices/DeviceList";
import SensorList from "../features/sensors/SensorList";

export default function DashboardPage() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-emerald-600">
          Phase 3
        </p>
        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Smart Greenhouse Dashboard
        </h2>
        <p className="mt-2 text-slate-600">
          Abstract Factory provisions coherent device families while keeping sensor creation reusable.
        </p>
      </div>

      <div id="devices">
        <DeviceList />
      </div>

      <div id="sensors">
        <SensorList />
      </div>
    </section>
  );
}