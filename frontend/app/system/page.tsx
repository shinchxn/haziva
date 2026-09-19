"use client";

import { useEffect, useState } from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Header from "@/components/layout/Header";
import SystemStatusCard from "@/components/dashboard/SystemStatusCard";

import { api } from "@/lib/api";
import type { SystemStatus } from "@/types/api";

export default function SystemStatusPage() {
  const [status, setStatus] =
    useState<SystemStatus | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadStatus() {
      try {
        setLoading(true);
        setError(null);

        const data = await api.getSystemStatus();

        setStatus(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load system status.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadStatus();
  }, []);

  return (
    <DashboardShell>
      <Header
        title="System Status"
        description="Model, data and forecast system availability"
      />

      <div className="space-y-8 p-8">
        {loading && (
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-slate-500">
              Loading system status...
            </p>
          </section>
        )}

        {error && (
          <section className="rounded-xl border border-red-200 bg-red-50 p-6">
            <h2 className="text-lg font-semibold text-red-800">
              Unable to load system status
            </h2>

            <p className="mt-2 text-sm text-red-700">
              {error}
            </p>
          </section>
        )}

        {!loading && !error && status && (
          <>
            <SystemStatusCard status={status} />

            <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">
                System Information
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Only information currently provided by the backend is shown here.
              </p>

              <div className="mt-6 grid gap-5 md:grid-cols-2">
                <div className="rounded-lg bg-slate-50 p-5">
                  <p className="text-sm text-slate-500">
                    Model Status
                  </p>

                  <p className="mt-1 text-lg font-semibold text-slate-900">
                    {status.model_status}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-5">
                  <p className="text-sm text-slate-500">
                    Data Status
                  </p>

                  <p className="mt-1 text-lg font-semibold text-slate-900">
                    {status.data_status}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-5">
                  <p className="text-sm text-slate-500">
                    Forecast Horizon
                  </p>

                  <p className="mt-1 text-lg font-semibold text-slate-900">
                    {status.forecast_horizon}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-50 p-5">
                  <p className="text-sm text-slate-500">
                    Last Update
                  </p>

                  <p className="mt-1 text-lg font-semibold text-slate-900">
                    {new Date(
                      status.last_update,
                    ).toLocaleString("en-IN", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </p>
                </div>
              </div>
            </section>
          </>
        )}

        {!loading && !error && !status && (
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              No system status available
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              The backend did not provide system status
              information.
            </p>
          </section>
        )}
      </div>
    </DashboardShell>
  );
}
