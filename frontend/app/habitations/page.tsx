"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import DashboardShell from "@/components/layout/DashboardShell";
import Header from "@/components/layout/Header";
import HabitationMap from "@/components/map/HabitationMap";
import RiskTrajectoryChart from "@/components/habitations/RiskTrajectoryChart";
import RelocationMap from "@/components/habitations/RelocationMap";

import { api } from "@/lib/api";

import type {
  HabitationDetail,
  HabitationSummary,
  RelocationProfile,
  RiskProfile,
  TrajectoryResponse,
} from "@/types/api";

function getRiskLevel(value: number) {
  if (value >= 0.75) {
    return {
      label: "High",
      className: "bg-red-50 text-red-700",
      dot: "bg-red-500",
    };
  }

  if (value >= 0.5) {
    return {
      label: "Elevated",
      className: "bg-amber-50 text-amber-700",
      dot: "bg-amber-500",
    };
  }

  return {
    label: "Lower",
    className: "bg-emerald-50 text-emerald-700",
    dot: "bg-emerald-500",
  };
}

function getTrajectoryStyle(trajectory: string) {
  const value = trajectory.toLowerCase();

  if (
    value.includes("critical") ||
    value.includes("rapid")
  ) {
    return "bg-red-50 text-red-700";
  }

  if (value.includes("increasing")) {
    return "bg-amber-50 text-amber-700";
  }

  if (value.includes("decreasing")) {
    return "bg-emerald-50 text-emerald-700";
  }

  return "bg-slate-100 text-slate-700";
}

function getPriorityStyle(priority: string) {
  const value = priority.toLowerCase();

  if (value.includes("immediate")) {
    return "bg-red-50 text-red-700";
  }

  if (value.includes("high")) {
    return "bg-orange-50 text-orange-700";
  }

  if (value.includes("medium")) {
    return "bg-amber-50 text-amber-700";
  }

  return "bg-emerald-50 text-emerald-700";
}

function HabitationDetails() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const selectedId = searchParams.get("id");

  const [habitations, setHabitations] = useState<
    HabitationSummary[]
  >([]);

  const [loadingHabitations, setLoadingHabitations] =
    useState(true);

  const [habitationListError, setHabitationListError] =
    useState<string | null>(null);

  const [habitation, setHabitation] =
    useState<HabitationDetail | null>(null);

  const [risk, setRisk] =
    useState<RiskProfile | null>(null);

  const [trajectory, setTrajectory] =
    useState<TrajectoryResponse | null>(null);

  const [relocation, setRelocation] =
    useState<RelocationProfile | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadHabitations() {
      try {
        setLoadingHabitations(true);
        setHabitationListError(null);

        const data = await api.getHabitations();

        setHabitations(data);
      } catch (err) {
        setHabitationListError(
          err instanceof Error
            ? err.message
            : "Unable to load habitations.",
        );
      } finally {
        setLoadingHabitations(false);
      }
    }

    loadHabitations();
  }, []);

  useEffect(() => {
    if (!selectedId) {
      return;
    }

    async function loadHabitationDetails() {
      try {
        setLoading(true);
        setError(null);

        const habitationId = selectedId;

        if (!habitationId) {
          return;
        }

        const [
          habitationData,
          riskData,
          trajectoryData,
          relocationData,
        ] = await Promise.all([
          api.getHabitation(habitationId),
          api.getHabitationRisk(habitationId),
          api.getHabitationTrajectory(habitationId),
          api.getHabitationRelocation(habitationId),
        ]);

        setHabitation(habitationData);
        setRisk(riskData);
        setTrajectory(trajectoryData);
        setRelocation(relocationData);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load habitation intelligence.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadHabitationDetails();
  }, [selectedId]);

  /*
   * Habitation Intelligence landing page
   */
  if (!selectedId) {
    return (
      <DashboardShell>
        <Header
          title="Habitation Intelligence"
          description="Review backend-provided risk and priority information for Wayanad habitations."
        />

        <div className="space-y-8 p-8">
          {loadingHabitations && (
            <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <p className="text-sm text-slate-500">
                Loading habitations...
              </p>
            </section>
          )}

          {habitationListError && (
            <section className="rounded-xl border border-red-200 bg-red-50 p-6">
              <h2 className="text-lg font-semibold text-red-800">
                Unable to load habitations
              </h2>

              <p className="mt-2 text-sm text-red-700">
                {habitationListError}
              </p>
            </section>
          )}

          {!loadingHabitations &&
            !habitationListError &&
            habitations.length === 0 && (
              <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900">
                  No habitations available
                </h2>

                <p className="mt-2 text-sm text-slate-500">
                  The backend did not return any habitation
                  records.
                </p>
              </section>
            )}

          {!loadingHabitations &&
            !habitationListError &&
            habitations.length > 0 && (
              <>
                <section>
                  <div className="mb-5">
                    <h2 className="text-xl font-semibold text-slate-900">
                      Habitation Overview
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                      Select a habitation to view its complete
                      risk, vulnerability and relocation
                      intelligence.
                    </p>
                  </div>

                  <div className="grid gap-5 lg:grid-cols-2">
                    {habitations.map((item) => {
                      const riskLevel = getRiskLevel(
                        item.current_risk,
                      );

                      const priorityClass =
                        getPriorityStyle(item.priority);

                      return (
                        <section
                          key={item.id}
                          className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                                Habitation
                              </p>

                              <h3 className="mt-1 text-xl font-semibold text-slate-900">
                                {item.name}
                              </h3>

                              <p className="mt-2 text-sm text-slate-500">
                                {item.latitude.toFixed(4)},{" "}
                                {item.longitude.toFixed(4)}
                              </p>
                            </div>

                            <span
                              className={`rounded-full px-3 py-1 text-xs font-semibold ${priorityClass}`}
                            >
                              {item.priority}
                            </span>
                          </div>

                          <div className="mt-6 grid grid-cols-2 gap-4">
                            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                              <p className="text-xs font-medium text-slate-500">
                                Current Risk
                              </p>

                              <div className="mt-2 flex items-center gap-2">
                                <p className="text-2xl font-bold text-slate-900">
                                  {(
                                    item.current_risk * 100
                                  ).toFixed(0)}
                                  %
                                </p>

                                <span
                                  className={`inline-flex items-center gap-1.5 rounded-full px-2 py-1 text-xs font-semibold ${riskLevel.className}`}
                                >
                                  <span
                                    className={`h-1.5 w-1.5 rounded-full ${riskLevel.dot}`}
                                  />
                                  {riskLevel.label}
                                </span>
                              </div>
                            </div>

                            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                              <p className="text-xs font-medium text-slate-500">
                                Priority
                              </p>

                              <p className="mt-2 text-lg font-semibold capitalize text-slate-900">
                                {item.priority}
                              </p>

                              <p className="mt-1 text-xs text-slate-500">
                                Backend-provided
                              </p>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() =>
                              router.push(
                                `/habitations?id=${item.id}`,
                              )
                            }
                            className="mt-6 w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                          >
                            View Habitation Intelligence
                          </button>
                        </section>
                      );
                    })}
                  </div>
                </section>

                <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="mb-5">
                    <h2 className="text-xl font-semibold text-slate-900">
                      Habitation Risk Map
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                      Select a habitation marker to open its
                      detailed intelligence.
                    </p>
                  </div>

                  <HabitationMap
                    habitations={habitations}
                    onSelect={(id) =>
                      router.push(
                        `/habitations?id=${id}`,
                      )
                    }
                  />
                </section>
              </>
            )}
        </div>
      </DashboardShell>
    );
  }

  /*
   * Loading detailed habitation intelligence
   */
  if (loading) {
    return (
      <DashboardShell>
        <Header
          title="Habitation Intelligence"
          description="Loading habitation risk and relocation intelligence"
        />

        <div className="p-8">
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-slate-500">
              Loading habitation intelligence...
            </p>
          </section>
        </div>
      </DashboardShell>
    );
  }

  /*
   * Error state
   */
  if (error) {
    return (
      <DashboardShell>
        <Header
          title="Habitation Intelligence"
          description="Unable to load habitation intelligence"
        />

        <div className="p-8">
          <section className="rounded-xl border border-red-200 bg-red-50 p-6">
            <h2 className="text-lg font-semibold text-red-800">
              Unable to load habitation
            </h2>

            <p className="mt-2 text-sm text-red-700">
              {error}
            </p>

            <button
              type="button"
              onClick={() =>
                router.push("/habitations")
              }
              className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            >
              Back to Habitations
            </button>
          </section>
        </div>
      </DashboardShell>
    );
  }

  /*
   * No-data state
   */
  if (!habitation || !risk || !trajectory || !relocation) {
    return (
      <DashboardShell>
        <Header
          title="Habitation Intelligence"
          description="No habitation intelligence available"
        />

        <div className="p-8">
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <h2 className="text-lg font-semibold text-slate-900">
              No habitation data available
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              The backend did not provide complete intelligence
              for this habitation.
            </p>

            <button
              type="button"
              onClick={() =>
                router.push("/habitations")
              }
              className="mt-5 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
            >
              Back to Habitations
            </button>
          </section>
        </div>
      </DashboardShell>
    );
  }

  const candidateSites = relocation.sites.filter(
    (site) =>
      site.status.toLowerCase() === "candidate",
  );

  const rejectedSites = relocation.sites.filter(
    (site) =>
      site.status.toLowerCase() === "rejected",
  );

  const selectedSummary = habitations.find(
    (item) => item.id === habitation.id,
  );

  const backendPriority =
    habitation.priority ||
    selectedSummary?.priority ||
    "Not provided";

  const currentRiskLevel = getRiskLevel(risk.current);

  return (
    <DashboardShell>
      <Header
        title={habitation.name}
        description="Habitation risk, trajectory, exposure, vulnerability and relocation intelligence"
      />

      <div className="space-y-8 p-8">
        <div>
          <button
            type="button"
            onClick={() =>
              router.push("/habitations")
            }
            className="text-sm font-semibold text-slate-600 transition hover:text-slate-900"
          >
            ← Back to Habitations
          </button>
        </div>

        {/* Overview */}
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Habitation Intelligence
                </p>

                <h2 className="mt-1 text-2xl font-bold text-slate-900">
                  {habitation.name}
                </h2>

                <p className="mt-2 text-sm text-slate-500">
                  Coordinates:{" "}
                  {habitation.latitude.toFixed(4)},{" "}
                  {habitation.longitude.toFixed(4)}
                </p>

                <div className="mt-4 flex flex-wrap gap-2">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${currentRiskLevel.className}`}
                  >
                    {currentRiskLevel.label} current risk
                  </span>

                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${getPriorityStyle(
                      backendPriority,
                    )}`}
                  >
                    Priority: {backendPriority}
                  </span>
                </div>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
                <p className="text-xs font-medium text-slate-500">
                  Hazard Type
                </p>

                <p className="mt-1 text-sm font-semibold capitalize text-slate-900">
                  {risk.hazard_type}
                </p>
              </div>
            </div>
          </div>

          <div className="grid gap-px bg-slate-200 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white p-5">
              <p className="text-xs font-medium text-slate-500">
                Current Risk
              </p>

              <p className="mt-2 text-3xl font-bold text-slate-900">
                {(risk.current * 100).toFixed(0)}%
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Current backend risk
              </p>
            </div>

            <div className="bg-white p-5">
              <p className="text-xs font-medium text-slate-500">
                24h Risk
              </p>

              <p className="mt-2 text-3xl font-bold text-slate-900">
                {(risk.risk_24h * 100).toFixed(0)}%
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Backend forecast
              </p>
            </div>

            <div className="bg-white p-5">
              <p className="text-xs font-medium text-slate-500">
                72h Risk
              </p>

              <p className="mt-2 text-3xl font-bold text-slate-900">
                {(risk.risk_72h * 100).toFixed(0)}%
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Backend forecast
              </p>
            </div>

            <div className="bg-white p-5">
              <p className="text-xs font-medium text-slate-500">
                Prediction Confidence
              </p>

              <p className="mt-2 text-3xl font-bold text-slate-900">
                {(risk.confidence * 100).toFixed(0)}%
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Separate from risk severity
              </p>
            </div>
          </div>
        </section>

        {/* Risk trajectory */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5 flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Forecast
              </p>

              <h2 className="mt-1 text-xl font-semibold text-slate-900">
                Risk Trajectory
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Backend-provided current and forecast risk over
                the available horizon.
              </p>
            </div>

            <span
              className={`w-fit rounded-full px-3 py-1.5 text-sm font-semibold ${getTrajectoryStyle(
                trajectory.trajectory,
              )}`}
            >
              {trajectory.trajectory}
            </span>
          </div>

          <RiskTrajectoryChart
            current={risk.current}
            risk24h={risk.risk_24h}
            risk72h={risk.risk_72h}
          />
        </section>

        {/* Risk drivers */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Explainability
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-900">
              Major Risk Drivers
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Drivers returned directly by the backend.
            </p>
          </div>

          {risk.drivers.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {risk.drivers.map((driver, index) => (
                <div
                  key={driver}
                  className="flex items-start gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4"
                >
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">
                    {index + 1}
                  </span>

                  <p className="pt-1 text-sm font-medium leading-5 text-slate-800">
                    {driver}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">
                No risk drivers were provided by the backend.
              </p>
            </div>
          )}
        </section>

        {/* Exposure */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Exposure
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-900">
              Exposed Population & Assets
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Backend-provided exposure information.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium text-slate-500">
                Population
              </p>

              <p className="mt-2 text-2xl font-bold text-slate-900">
                {habitation.population}
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium text-slate-500">
                Households
              </p>

              <p className="mt-2 text-2xl font-bold text-slate-900">
                {habitation.households}
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium text-slate-500">
                Population Exposure
              </p>

              <p className="mt-2 text-lg font-semibold text-slate-900">
                {habitation.exposure_info.population_exposure}
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium text-slate-500">
                Landslide Susceptibility
              </p>

              <p className="mt-2 text-lg font-semibold text-slate-900">
                {
                  habitation.exposure_info
                    .landslide_susceptibility
                }
              </p>
            </div>
          </div>

          <div className="mt-4 rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-medium text-slate-500">
                  Exposure Score
                </p>

                <p className="mt-1 text-sm text-slate-500">
                  Backend-provided score
                </p>
              </div>

              <p className="text-xl font-bold text-slate-900">
                {(
                  habitation.exposure_info.score * 100
                ).toFixed(0)}
                %
              </p>
            </div>
          </div>
        </section>

        {/* Vulnerability and accessibility */}
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Vulnerability
              </p>

              <h2 className="mt-1 text-xl font-semibold text-slate-900">
                Vulnerability Indicators
              </h2>
            </div>

            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">
                  Socioeconomic Vulnerability
                </p>

                <p className="mt-2 font-semibold text-slate-900">
                  {
                    habitation.vulnerability_info
                      .socioeconomic_vulnerability
                  }
                </p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">
                  Health Access
                </p>

                <p className="mt-2 font-semibold text-slate-900">
                  {
                    habitation.vulnerability_info
                      .health_access
                  }
                </p>
              </div>

              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
                <div>
                  <p className="text-xs font-medium text-slate-500">
                    Vulnerability Score
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    Backend-provided score
                  </p>
                </div>

                <p className="text-xl font-bold text-slate-900">
                  {(
                    habitation.vulnerability_info.score *
                    100
                  ).toFixed(0)}
                  %
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Accessibility
              </p>

              <h2 className="mt-1 text-xl font-semibold text-slate-900">
                Evacuation & Access
              </h2>
            </div>

            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">
                  Road Access
                </p>

                <p className="mt-2 font-semibold text-slate-900">
                  {habitation.accessibility_info.road_access}
                </p>
              </div>

              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs font-medium text-slate-500">
                  Evacuation Route
                </p>

                <p className="mt-2 font-semibold text-slate-900">
                  {
                    habitation.accessibility_info
                      .evacuation_route
                  }
                </p>
              </div>

              <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
                <div>
                  <p className="text-xs font-medium text-slate-500">
                    Accessibility Score
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    Backend-provided score
                  </p>
                </div>

                <p className="text-xl font-bold text-slate-900">
                  {(
                    habitation.accessibility_info.score *
                    100
                  ).toFixed(0)}
                  %
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Priority */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Decision Support
              </p>

              <h2 className="mt-1 text-xl font-semibold text-slate-900">
                Assessment Priority
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Priority is provided by the backend decision-support
                system.
              </p>
            </div>

            <span
              className={`w-fit rounded-full px-4 py-2 text-sm font-semibold ${getPriorityStyle(
                backendPriority,
              )}`}
            >
              {backendPriority}
            </span>
          </div>
        </section>

        {/* Relocation */}
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Relocation Intelligence
            </p>

            <h2 className="mt-1 text-xl font-semibold text-slate-900">
              Candidate Relocation Sites
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Backend-provided candidate and rejected relocation
              sites.
            </p>
          </div>

          <RelocationMap
            habitation={habitation}
            sites={relocation.sites}
          />

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-medium text-slate-500">
                Total Sites
              </p>

              <p className="mt-2 text-2xl font-bold text-slate-900">
                {relocation.sites.length}
              </p>
            </div>

            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4">
              <p className="text-xs font-medium text-emerald-700">
                Candidate Sites
              </p>

              <p className="mt-2 text-2xl font-bold text-emerald-800">
                {candidateSites.length}
              </p>
            </div>

            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="text-xs font-medium text-red-700">
                Rejected Sites
              </p>

              <p className="mt-2 text-2xl font-bold text-red-800">
                {rejectedSites.length}
              </p>
            </div>
          </div>

          <div className="mt-6 space-y-4">
            {relocation.sites.length === 0 ? (
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-5">
                <p className="text-sm text-slate-500">
                  No relocation sites were provided by the backend.
                </p>
              </div>
            ) : (
              relocation.sites.map((site) => {
                const isCandidate =
                  site.status.toLowerCase() ===
                  "candidate";

                return (
                  <div
                    key={site.site_id}
                    className="rounded-xl border border-slate-200 p-5 transition-shadow hover:shadow-sm"
                  >
                    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <span
                            className={`h-2.5 w-2.5 rounded-full ${
                              isCandidate
                                ? "bg-emerald-500"
                                : "bg-red-500"
                            }`}
                          />

                          <h3 className="font-semibold text-slate-900">
                            {site.site_id}
                          </h3>
                        </div>

                        <p className="mt-2 text-sm text-slate-500">
                          Accessibility:{" "}
                          {site.accessibility ??
                            "Not provided"}
                        </p>
                      </div>

                      <span
                        className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ${
                          isCandidate
                            ? "bg-emerald-50 text-emerald-700"
                            : "bg-red-50 text-red-700"
                        }`}
                      >
                        {site.status}
                      </span>
                    </div>

                    <div className="mt-5 grid gap-4 border-t border-slate-100 pt-5 sm:grid-cols-3">
                      <div>
                        <p className="text-xs font-medium text-slate-500">
                          Safety
                        </p>

                        <p className="mt-1 font-semibold text-slate-900">
                          {site.safety}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-slate-500">
                          Capacity
                        </p>

                        <p className="mt-1 font-semibold text-slate-900">
                          {site.capacity}
                        </p>
                      </div>

                      <div>
                        <p className="text-xs font-medium text-slate-500">
                          Infrastructure
                        </p>

                        <p className="mt-1 font-semibold capitalize text-slate-900">
                          {site.infrastructure
                            ? Object.entries(
                                site.infrastructure,
                              )
                                .filter(
                                  ([, value]) =>
                                    value === true,
                                )
                                .map(([key]) => key)
                                .join(", ") ||
                              "Not provided"
                            : "Not provided"}
                        </p>
                      </div>
                    </div>

                    {site.rejection_reason && (
                      <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-red-700">
                          Rejection Reason
                        </p>

                        <p className="mt-1 text-sm leading-5 text-red-800">
                          {site.rejection_reason}
                        </p>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </section>
      </div>
    </DashboardShell>
  );
}

export default function HabitationsPage() {
  return (
    <Suspense
      fallback={
        <DashboardShell>
          <Header
            title="Habitation Intelligence"
            description="Loading habitation intelligence"
          />

          <div className="p-8">
            <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <p className="text-sm text-slate-500">
                Loading...
              </p>
            </section>
          </div>
        </DashboardShell>
      }
    >
      <HabitationDetails />
    </Suspense>
  );
}