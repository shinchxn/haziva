"use client";

import type { SystemStatus } from "@/types/api";

interface SystemStatusCardProps {
  status: SystemStatus;
}

export default function SystemStatusCard({
  status,
}: SystemStatusCardProps) {
  const lastUpdated = new Date(status.last_update);

  const formattedLastUpdate = lastUpdated.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });

  const isReady =
    status.model_status.toLowerCase() === "ready";

  const isAvailable =
    status.data_status.toLowerCase() === "available";

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            System Status
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Current model, data and forecast availability
          </p>
        </div>

        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            isReady && isAvailable
              ? "bg-emerald-50 text-emerald-700"
              : "bg-amber-50 text-amber-700"
          }`}
        >
          {isReady && isAvailable
            ? "Operational"
            : "Check Status"}
        </span>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-500">
            Model Status
          </p>

          <p className="mt-1 text-lg font-semibold capitalize text-slate-900">
            {status.model_status}
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-500">
            Data Status
          </p>

          <p className="mt-1 text-lg font-semibold capitalize text-slate-900">
            {status.data_status}
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-500">
            Forecast Horizon
          </p>

          <p className="mt-1 text-lg font-semibold text-slate-900">
            {status.forecast_horizon}
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-500">
            Last Update
          </p>

          <p className="mt-1 text-sm font-semibold text-slate-900">
            {formattedLastUpdate}
          </p>
        </div>
      </div>
    </section>
  );
}
