import { useCallback, useState } from "react";
import EventFeed from "../components/alerts/EventFeed";
import CommandPanel from "../components/commands/CommandPanel";
import LocationConfigWizard from "../components/config/LocationConfigWizard";
import DeviceList from "../components/devices/DeviceList";
import ExecutionLog from "../features/actuators/ExecutionLog";
import StrategyPanel from "../features/automation/StrategyPanel";
import OverviewPanel from "../features/overview/OverviewPanel";
import SensorList from "../features/sensors/SensorList";

export default function DashboardPage() {
  // Bumped after any location, zone, assignment, strategy or command change, so every
  // section that depends on those reloads its data.
  const [version, setVersion] = useState(0);
  const handleChanged = useCallback(() => setVersion((current) => current + 1), []);

  return (
    <section className="space-y-6">
      <div>
        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Smart Greenhouse Dashboard
        </h2>
        <p className="mt-2 text-slate-600">
          Location overview, configuration, devices, actuator controls, actuator executions, event feed, sensors and automation.
        </p>
      </div>

      <div id="overview">
        <OverviewPanel version={version} />
      </div>

      <div id="configuration">
        <LocationConfigWizard version={version} onChanged={handleChanged} />
      </div>

      <div id="devices">
        <DeviceList version={version} onChanged={handleChanged} />
      </div>

      <div id="controls">
        <CommandPanel version={version} onChanged={handleChanged} />
      </div>

      <div id="executions">
        <ExecutionLog />
      </div>

      <div id="events">
        <EventFeed version={version} />
      </div>

      <div id="sensors">
        <SensorList version={version} />
      </div>

      <div id="automation">
        <StrategyPanel version={version} onChanged={handleChanged} />
      </div>
    </section>
  );
}
