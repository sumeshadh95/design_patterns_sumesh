import { useEffect, useState } from "react";
import {
  fetchDevices,
  provisionDeviceFamily,
  type DeviceDto,
  type DeviceFamily,
} from "../../services/api";
import ActuatorStateBadge from "./ActuatorStateBadge";
import ActuatorStateControl from "./ActuatorStateControl";
import DeviceFamilySwitcher from "./DeviceFamilySwitcher";

export default function DeviceList() {
  const [family, setFamily] = useState<DeviceFamily>("simulation");
  const [devices, setDevices] = useState<DeviceDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [provisioning, setProvisioning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDevices = async (selectedFamily: DeviceFamily) => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchDevices({ family: selectedFamily });
      setDevices(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load devices");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let mounted = true;

    async function loadFamily() {
      try {
        const data = await fetchDevices({ family });

        if (mounted) {
          setDevices(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err.message : "Failed to load devices");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadFamily();

    return () => {
      mounted = false;
    };
  }, [family]);

  const handleFamilyChange = (nextFamily: DeviceFamily) => {
    setLoading(true);
    setFamily(nextFamily);
  };


  const handleProvision = async () => {
    try {
      setProvisioning(true);
      setError(null);
      await provisionDeviceFamily(family);
      await loadDevices(family);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to provision family");
    } finally {
      setProvisioning(false);
    }
  };

  const handleDeviceChanged = (updated: DeviceDto) => {
    setDevices((current) =>
      current.map((device) => (device.id === updated.id ? updated : device)),
    );
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-xl font-semibold text-slate-900">Devices</h3>
          <p className="text-sm text-slate-600">
            Provision and inspect device families
          </p>
        </div>

        <div className="flex items-center gap-2">
          <DeviceFamilySwitcher selectedFamily={family} onChange={handleFamilyChange} />
          <button
            type="button"
            onClick={() => void handleProvision()}
            disabled={provisioning}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {provisioning ? "Provisioning..." : "Provision family"}
          </button>
        </div>
      </div>

      <div className="mt-6">
        {loading && <p className="text-slate-600">Loading devices...</p>}

        {!loading && error && (
          <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </p>
        )}

        {!loading && !error && devices.length === 0 && (
          <p className="text-sm text-slate-500">No devices found for this family.</p>
        )}

        {!loading && !error && devices.length > 0 && (
          <div className="grid gap-3 md:grid-cols-2">
            {devices.map((device) => (
              <article
                key={device.id}
                className="rounded-xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-semibold text-slate-900">{device.display_name}</h4>
                  <div className="flex gap-2">
                    {device.state && (
                      <ActuatorStateBadge
                        state={device.state}
                        allowedCommands={device.allowed_commands}
                      />
                    )}
                    <span className="rounded-full bg-slate-200 px-2 py-1 text-xs font-medium text-slate-700">
                      {device.role}
                    </span>
                    <span className="rounded-full bg-indigo-100 px-2 py-1 text-xs font-medium text-indigo-700">
                      {device.device_family}
                    </span>
                  </div>
                </div>
                <p className="mt-2 text-sm text-slate-600">{device.device_type}</p>
                <p className="mt-2 text-xs text-slate-500 break-all">ID: {device.id}</p>

                {device.state && (
                  <ActuatorStateControl
                    device={device}
                    onChanged={handleDeviceChanged}
                  />
                )}
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
