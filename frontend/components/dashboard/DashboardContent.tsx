"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { api } from "@/lib/api";
import type {
  HabitationSummary,
  RiskProfile,
  SystemStatus,
} from "@/types/api";

import RiskSummary from "./RiskSummary";
import SystemStatusCard from "./SystemStatusCard";
import HabitationMap from "@/components/map/HabitationMap";

export default function DashboardContent() {
  const router = useRouter();

  const [habitations, setHabitations] = useState<
    HabitationSummary[]
  >([]);

  const [systemStatus, setSystemStatus] =
    useState<SystemStatus | null>(null);

  const [riskData, setRiskData] = useState<
    Record<string, RiskProfile>
  >({});

  const [selectedId, setSelectedId] = useState<
    string | null
  >(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(
    null,
  );

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [habitationData, statusData] =
          await Promise.all([
            api.getHabitations(),
            api.getSystemStatus(),
          ]);

        setHabitations(habitationData);
        setSystemStatus(statusData);

        const riskEntries = await Promise.all(
          habitationData.map(async (habitation) => {
            try {
              const risk = await api.getRisk(
                habitation.id,
              );

              return [habitation.id, risk] as const;
            } catch {
              return null;
            }
          }),
        );

        const risks: Record<string, RiskProfile> = {};

        riskEntries.forEach((entry) => {
          if (entry) {
            const [id, risk] = entry;
            risks[id] = risk;
          }
        });

        setRiskData(risks);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load dashboard data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <p className="text-sm text-slate-500">
            Loading Wayanad risk dashboard...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <h2 className="text-lg font-semibold text-red-800">
          Unable to load dashboard
        </h2>

        <p className="mt-2 text-sm text-red-700">
          {error}
        </p>
      </div>
    );
  }

  if (habitations.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">
          No habitation data available
        </h2>

        <p className="mt-2 text-sm text-slate-500">
          The backend did not return any habitation records.
        </p>
      </div>
    );
  }

  const highPriorityCount = habitations.filter(
    (habitation) =>
      habitation.priority.toLowerCase() === "high",
  ).length;

  const immediateAssessmentCount = habitations.filter(
    (habitation) =>
      habitation.priority
        .toLowerCase()
        .includes("immediate"),
  ).length;

  const priorityHabitation =
    habitations.find(
      (habitation) =>
        habitation.priority.toLowerCase() === "high",
    ) ?? null;

  return (
    <div className="space-y-8">
      {/* Risk Summary */}
      <RiskSummary
        highPriorityCount={highPriorityCount}
        immediateAssessmentCount={
          immediateAssessmentCount
        }
        systemStatus={
          systemStatus
            ? systemStatus.model_status
            : "Unavailable"
        }
      />

      {/* Priority Habitation */}
      {priorityHabitation && (
        <section>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-900">
              Priority & Decision Support
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Start with the highest-priority habitation and open its
              detailed risk, trajectory and relocation intelligence.
            </p>
          </div>

          <div className="rounded-xl border border-orange-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-center">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-orange-600">
                  Priority Habitation
                </p>

                <h2 className="mt-1 text-2xl font-bold text-slate-900">
                  {priorityHabitation.name}
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Backend-provided priority:{" "}
                  <span className="font-medium text-orange-700">
                    {priorityHabitation.priority}
                  </span>
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="rounded-lg bg-orange-50 px-5 py-3">
                  <p className="text-xs font-semibold text-orange-700">
                    Baseline Susceptibility
                  </p>

                  <p className="text-2xl font-bold text-orange-800">
                    {(
                      priorityHabitation.current_risk * 100
                    ).toFixed(0)}
                    %
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    router.push(
                      `/habitations?id=${priorityHabitation.id}`,
                    )
                  }
                  className="rounded-lg bg-slate-900 px-5 py-3 text-sm font-medium text-white transition hover:bg-slate-800"
                >
                  View Intelligence
                </button>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* System Status */}
      {systemStatus && (
        <SystemStatusCard status={systemStatus} />
      )}

      {/* Habitation Map */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-5">
          <h2 className="text-lg font-semibold text-slate-900">
            Habitation Risk Map
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Select a habitation to view its detailed risk,
            trajectory and relocation intelligence.
          </p>
        </div>

        <HabitationMap
          habitations={habitations}
          selectedId={selectedId}
          onSelect={(id) => {
            setSelectedId(id);
            router.push(`/habitations?id=${id}`);
          }}
        />
      </section>

      {/* Habitation Overview */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="mb-5">
          <h2 className="text-lg font-semibold text-slate-900">
            Habitation Overview
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Current backend-provided priority and risk for
            monitored habitations.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-semibold">
                  Habitation
                </th>

                <th className="px-4 py-3 font-semibold">
                  Baseline Susceptibility
                </th>

                <th className="px-4 py-3 font-semibold">
                  Risk Level
                </th>

                <th className="px-4 py-3 font-semibold">
                  Priority
                </th>

                <th className="px-4 py-3 font-semibold">
                  Action
                </th>
              </tr>
            </thead>

            <tbody>
              {habitations.map((habitation) => {
                const risk = riskData[habitation.id];

                const riskValue =
                  risk?.current ?? null;

                const riskLevel =
                  riskValue === null
                    ? "Unavailable"
                    : riskValue >= 0.75
                      ? "High"
                      : riskValue >= 0.5
                        ? "Elevated"
                        : "Lower";

                const riskBadge =
                  riskValue === null
                    ? "bg-slate-100 text-slate-600"
                    : riskValue >= 0.75
                      ? "bg-red-50 text-red-700"
                      : riskValue >= 0.5
                        ? "bg-amber-50 text-amber-700"
                        : "bg-emerald-50 text-emerald-700";

                const priorityBadge =
                  habitation.priority.toLowerCase() ===
                  "high"
                    ? "bg-orange-50 text-orange-700"
                    : "bg-slate-100 text-slate-700";

                return (
                  <tr
                    key={habitation.id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50"
                  >
                    <td className="px-4 py-4 font-medium text-slate-900">
                      {habitation.name}
                    </td>

                    <td className="px-4 py-4">
                      <span className="font-semibold text-slate-900">
                        {riskValue !== null
                          ? `${(
                              riskValue * 100
                            ).toFixed(0)}%`
                          : "Unavailable"}
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${riskBadge}`}
                      >
                        {riskLevel}
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <span
                        className={`rounded-full px-3 py-1 text-xs font-semibold ${priorityBadge}`}
                      >
                        {habitation.priority}
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedId(habitation.id);
                          router.push(
                            `/habitations?id=${habitation.id}`,
                          );
                        }}
                        className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 transition hover:border-slate-400 hover:bg-slate-50"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}