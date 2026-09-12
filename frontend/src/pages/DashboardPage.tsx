import SensorList from "../features/sensors/SensorList";

const sections = [
  {
    id: "sensors",
    title: "Sensors",
    description: "Sensor functionality is managed here.",
  },
  {
    id: "config",
    title: "Configuration",
    description: "Greenhouse configuration will be added later.",
  },
  {
    id: "automation",
    title: "Automation",
    description: "Automation functionality will be added later.",
  },
  {
    id: "overview",
    title: "Overview",
    description: "System overview functionality will be added later.",
  },
  {
    id: "controls",
    title: "Controls",
    description: "Greenhouse controls will be added later.",
  },
  {
    id: "events",
    title: "Events",
    description: "Greenhouse event functionality will be added later.",
  },
];

export default function DashboardPage() {
  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-emerald-600">
          Phase 2
        </p>

        <h2 className="mt-2 text-3xl font-bold text-slate-900">
          Smart Greenhouse Dashboard
        </h2>

        <p className="mt-2 text-slate-600">
          Sensors are created through the Factory Method and stored in the devices table.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
        {sections.map((section) => (
          <article
            key={section.id}
            id={section.id}
            className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
          >
            <h3 className="text-lg font-semibold text-slate-900">
              {section.title}
            </h3>

            <p className="mt-2 text-sm leading-6 text-slate-600">
              {section.description}
            </p>

            {section.id === "sensors" ? (
              <div className="mt-4">
                <SensorList />
              </div>
            ) : (
              <span className="mt-4 inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                Phase 2 placeholder
              </span>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}