import type { ZoneFields } from "./zoneForm";

type Props = {
  fields: ZoneFields;
  onChange: (fields: ZoneFields) => void;
  idPrefix: string;
};

const inputClass = "w-full rounded-lg border border-slate-300 px-3 py-2 text-sm";

export default function ZoneFieldsInputs({ fields, onChange, idPrefix }: Props) {
  const set = (key: keyof ZoneFields) => (event: React.ChangeEvent<HTMLInputElement>) =>
    onChange({ ...fields, [key]: event.target.value });

  return (
    <div className="grid gap-3 md:grid-cols-4">
      <label className="text-xs font-medium text-slate-600">
        Zone name
        <input
          id={`${idPrefix}-name`}
          value={fields.name}
          onChange={set("name")}
          className={inputClass}
          placeholder="Bench 1"
        />
      </label>
      <label className="text-xs font-medium text-slate-600">
        Moisture low
        <input
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={fields.low}
          onChange={set("low")}
          className={inputClass}
        />
      </label>
      <label className="text-xs font-medium text-slate-600">
        Moisture high
        <input
          type="number"
          min="0"
          max="1"
          step="0.01"
          value={fields.high}
          onChange={set("high")}
          className={inputClass}
        />
      </label>
      <label className="text-xs font-medium text-slate-600">
        Watering time
        <input
          type="time"
          value={fields.watering}
          onChange={set("watering")}
          className={inputClass}
        />
      </label>
    </div>
  );
}
