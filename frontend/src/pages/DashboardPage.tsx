import LocationConfigWizard from "../components/config/LocationConfigWizard";
import DeviceList from "../components/devices/DeviceList";
import SensorList from "../features/sensors/SensorList";

export default function DashboardPage() {
  return (
    <section className="space-y-6">
      <div>
              
        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Smart Greenhouse Dashboard
        </h2>
        <p className="mt-2 text-slate-600">
          Builder creates valid location configurations with one or more zones.
        </p>
      </div>

      <div id="config">
        <LocationConfigWizard />
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