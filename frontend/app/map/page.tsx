"use client";

import { useEffect, useState } from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Header from "@/components/layout/Header";
import HabitationMap from "@/components/map/HabitationMap";

import { api } from "@/lib/api";
import type { HabitationSummary } from "@/types/api";

export default function MapPage() {
  const [habitations, setHabitations] = useState<
    HabitationSummary[]
  >([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadHabitations() {
      try {
        setLoading(true);
        setError(null);

        const data = await api.getHabitations();

        setHabitations(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load habitation map data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadHabitations();
  }, []);

  return (
    <DashboardShell>
      <Header
        title="Habitation Risk Map"
        description="Interactive map of Wayanad habitation risk and priority"
      />

      <div className="space-y-8 p-8">
        {loading && (
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-slate-500">
              Loading habitation risk map...
            </p>
          </section>
        )}

        {error && (
          <section className="rounded-xl border border-red-200 bg-red-50 p-6">
            <h2 className="text-lg font-semibold text-red-800">
              Unable to load habitation map
            </h2>

            <p className="mt-2 text-sm text-red-700">
              {error}
            </p>
          </section>
        )}

        {!loading &&
          !error &&
          habitations.length === 0 && (
            <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <h2 className="text-lg font-semibold text-slate-900">
                No habitation data available
              </h2>

              <p className="mt-2 text-sm text-slate-500">
                The backend did not return any habitation
                records.
              </p>
            </section>
          )}

        {!loading &&
          !error &&
          habitations.length > 0 && (
            <>
              <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-5">
                  <h2 className="text-lg font-semibold text-slate-900">
                    Wayanad Habitation Risk Map
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Select a habitation marker to open its
                    risk, trajectory and relocation
                    intelligence.
                  </p>
                </div>

                <HabitationMap
                  habitations={habitations}
                  selectedId={null}
                  onSelect={() => {}}
                />
              </section>

              <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="mb-5">
                  <h2 className="text-lg font-semibold text-slate-900">
                    Map Summary
                  </h2>

                  <p className="mt-1 text-sm text-slate-500">
                    Backend-provided habitation records
                    currently displayed on the map.
                  </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-lg bg-slate-50 p-4">
                    <p className="text-xs font-medium text-slate-500">
                      Total Habitations
                    </p>

                    <p className="mt-1 text-2xl font-semibold text-slate-900">
                      {habitations.length}
                    </p>
                  </div>

                  <div className="rounded-lg bg-orange-50 p-4">
                    <p className="text-xs font-medium text-orange-700">
                      High Priority
                    </p>

                    <p className="mt-1 text-2xl font-semibold text-orange-900">
                      {
                        habitations.filter(
                          (habitation) =>
                            habitation.priority
                              .toLowerCase() ===
                            "high",
                        ).length
                      }
                    </p>
                  </div>

                  <div className="rounded-lg bg-amber-50 p-4">
                    <p className="text-xs font-medium text-amber-700">
                      Medium Priority
                    </p>

                    <p className="mt-1 text-2xl font-semibold text-amber-900">
                      {
                        habitations.filter(
                          (habitation) =>
                            habitation.priority
                              .toLowerCase() ===
                            "medium",
                        ).length
                      }
                    </p>
                  </div>

                  <div className="rounded-lg bg-slate-50 p-4">
                    <p className="text-xs font-medium text-slate-500">
                      Map Coverage
                    </p>

                    <p className="mt-1 text-2xl font-semibold text-slate-900">
                      Active
                    </p>
                  </div>
                </div>
              </section>
            </>
          )}
      </div>
    </DashboardShell>
  );
}
