import { BrowserRouter, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import DashboardPage from "./pages/DashboardPage";

function HomePage() {
  return (
    <section className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-emerald-600">
          Smart Greenhouse
        </p>

        <h2 className="mt-2 text-4xl font-bold text-slate-900">
          Three-Tier Application
        </h2>

        <p className="mt-4 max-w-2xl text-slate-600">
          Phase 1 foundation using FastAPI, PostgreSQL, Alembic,
          React, TypeScript and Tailwind CSS.
        </p>
      </div>
    </section>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}