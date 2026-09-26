import type { DeviceFamily } from "../../services/api";

type Props = {
  selectedFamily: DeviceFamily;
  onChange: (family: DeviceFamily) => void;
};

export default function DeviceFamilySwitcher({ selectedFamily, onChange }: Props) {
  const families: DeviceFamily[] = ["simulation", "edge"];

  return (
    <div className="inline-flex rounded-lg border border-slate-200 bg-white p-1">
      {families.map((family) => {
        const active = selectedFamily === family;
        return (
          <button
            key={family}
            type="button"
            onClick={() => onChange(family)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
              active
                ? "bg-emerald-600 text-white"
                : "text-slate-700 hover:bg-slate-100"
            }`}
          >
            {family}
          </button>
        );
      })}
    </div>
  );
}