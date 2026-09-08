import { NavLink, Outlet } from "react-router-dom";
import HealthStatus from "./HealthStatus";

export default function AppLayout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-lg font-bold text-slate-900">
              Smart Greenhouse
            </h1>

            <p className="text-sm text-slate-500">
              XAMK Design Patterns Project
            </p>
          </div>

          <div className="flex items-center gap-6">
            <nav className="flex gap-4 text-sm font-medium">
              <NavLink
                to="/"
                className={({ isActive }) =>
                  isActive
                    ? "text-emerald-600"
                    : "text-slate-600"
                }
              >
                Home
              </NavLink>

              <NavLink
                to="/dashboard"
                className={({ isActive }) =>
                  isActive
                    ? "text-emerald-600"
                    : "text-slate-600"
                }
              >
                Dashboard
              </NavLink>
            </nav>

            <HealthStatus />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}