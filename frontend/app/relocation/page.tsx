"use client";

import { useEffect, useState } from "react";

import DashboardShell from "@/components/layout/DashboardShell";
import Header from "@/components/layout/Header";
import RelocationMap from "@/components/habitations/RelocationMap";

import { api } from "@/lib/api";
import type {
  HabitationDetail,
  HabitationSummary,
  RelocationProfile,
} from "@/types/api";

export default function RelocationPage() {
  const [habitations, setHabitations] = useState<
    HabitationSummary[]
  >([]);

  const [selectedHabitationId, setSelectedHabitationId] =
    useState<string>("");

  const [habitation, setHabitation] =
    useState<HabitationDetail | null>(null);

  const [relocation, setRelocation] =
    useState<RelocationProfile | null>(null);

  const [loadingHabitations, setLoadingHabitations] =
    useState(true);

  const [loadingRelocation, setLoadingRelocation] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadHabitations() {
      try {
        setLoadingHabitations(true);
        setError(null);

        const data = await api.getHabitations();

        setHabitations(data);

        if (data.length > 0) {
          setSelectedHabitationId(data[0].id);
        }
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load habitation data.",
        );
      } finally {
        setLoadingHabitations(false);
      }
    }

    loadHabitations();
  }, []);

  useEffect(() => {
    if (!selectedHabitationId) {
      return;
    }

    async function loadRelocationData() {
      try {
        setLoadingRelocation(true);
        setError(null);

        const [habitationData, relocationData] =
          await Promise.all([
            api.getHabitation(selectedHabitationId),
            api.getHabitationRelocation(
              selectedHabitationId,
            ),
          ]);

        setHabitation(habitationData);
        setRelocation(relocationData);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load relocation data.",
        );

        setHabitation(null);
        setRelocation(null);
      } finally {
        setLoadingRelocation(false);
      }
    }

    loadRelocationData();
  }, [selectedHabitationId]);

  const candidateSites =
    relocation?.sites.filter(
      (site) =>
        site.status.toLowerCase() === "candidate",
    ) ?? [];

  const rejectedSites =
    relocation?.sites.filter(
      (site) =>
        site.status.toLowerCase() === "rejected",
    ) ?? [];

  return (
    <DashboardShell>
      <Header
        title="Relocation Intelligence"
        description="Backend-provided candidate and rejected relocation sites"
      />

      <div className="space-y-8 p-8">
        {loadingHabitations && (
          <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
            <p className="text-sm text-slate-500">
              Loading relocation intelligence...
            </p>
          </section>
        )}

        {error && (
          <section className="rounded-xl border border-red-200 bg-red-50 p-6">
            <h2 className="text-lg font-semibold text-red-800">
              Unable to load relocation data
            </h2>

            <p className="mt-2 text-sm text-red-700">
              {error}
            </p>
          </section>
        )}

        {!loadingHabitations &&
          !error &&
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
          !error &&
          habitations.length > 0 && (
            <>
              <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">
                      Select Habitation
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                      View relocation sites associated with
                      a backend habitation record.
                    </p>
                  </div>

                  <div className="w-full md:w-80">
                    <label
                      htmlFor="habitation-select"
                      className="mb-2 block text-sm font-medium text-slate-700"
                    >
                      Habitation
                    </label>

                    <select
                      id="habitation-select"
                      value={selectedHabitationId}
                      onChange={(event) =>
                        setSelectedHabitationId(
                          event.target.value,
                        )
                      }
                      className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                    >
                      {habitations.map(
                        (item) => (
                          <option
                            key={item.id}
                            value={item.id}
                          >
                            {item.name}
                          </option>
                        ),
                      )}
                    </select>
                  </div>
                </div>
              </section>

              {loadingRelocation && (
                <section className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                  <p className="text-sm text-slate-500">
                    Loading relocation sites...
                  </p>
                </section>
              )}

              {!loadingRelocation &&
                habitation &&
                relocation && (
                  <>
                    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                        <p className="text-xs font-medium text-slate-500">
                          Selected Habitation
                        </p>

                        <p className="mt-2 text-lg font-semibold text-slate-900">
                          {habitation.name}
                        </p>
                      </div>

                      <div className="rounded-xl border border-green-200 bg-green-50 p-5 shadow-sm">
                        <p className="text-xs font-medium text-green-700">
                          Candidate Sites
                        </p>

                        <p className="mt-2 text-2xl font-semibold text-green-900">
                          {candidateSites.length}
                        </p>
                      </div>

                      <div className="rounded-xl border border-red-200 bg-red-50 p-5 shadow-sm">
                        <p className="text-xs font-medium text-red-700">
                          Rejected Sites
                        </p>

                        <p className="mt-2 text-2xl font-semibold text-red-900">
                          {rejectedSites.length}
                        </p>
                      </div>

                      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                        <p className="text-xs font-medium text-slate-500">
                          Total Sites
                        </p>

                        <p className="mt-2 text-2xl font-semibold text-slate-900">
                          {relocation.sites.length}
                        </p>
                      </div>
                    </section>

                    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                      <div className="mb-5">
                        <h2 className="text-lg font-semibold text-slate-900">
                          Relocation Site Map
                        </h2>

                        <p className="mt-1 text-sm text-slate-500">
                          Candidate and rejected sites provided
                          by the backend.
                        </p>
                      </div>

                      <RelocationMap
                        habitation={habitation}
                        sites={relocation.sites}
                      />
                    </section>

                    <section className="grid gap-6 lg:grid-cols-2">
                      <div className="rounded-xl border border-green-200 bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <h2 className="text-lg font-semibold text-slate-900">
                              Candidate Sites
                            </h2>

                            <p className="mt-1 text-sm text-slate-500">
                              Sites marked as candidates by the
                              backend.
                            </p>
                          </div>

                          <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
                            {candidateSites.length}
                          </span>
                        </div>

                        <div className="mt-5 space-y-4">
                          {candidateSites.map(
                            (site) => (
                              <div
                                key={site.site_id}
                                className="rounded-lg border border-slate-200 p-4"
                              >
                                <div className="flex items-start justify-between gap-4">
                                  <div>
                                    <h3 className="font-semibold text-slate-900">
                                      {site.site_id}
                                    </h3>

                                    <p className="mt-1 text-sm text-slate-500">
                                      Accessibility:{" "}
                                      {site.accessibility ??
                                        "Not provided"}
                                    </p>
                                  </div>

                                  <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
                                    Candidate
                                  </span>
                                </div>

                                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                                  <div className="rounded-lg bg-slate-50 p-3">
                                    <p className="text-xs text-slate-500">
                                      Safety
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-slate-900">
                                      {site.safety}
                                    </p>
                                  </div>

                                  <div className="rounded-lg bg-slate-50 p-3">
                                    <p className="text-xs text-slate-500">
                                      Capacity
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-slate-900">
                                      {site.capacity}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            ),
                          )}

                          {candidateSites.length ===
                            0 && (
                            <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">
                              No candidate sites were
                              provided by the backend.
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="rounded-xl border border-red-200 bg-white p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <h2 className="text-lg font-semibold text-slate-900">
                              Rejected Sites
                            </h2>

                            <p className="mt-1 text-sm text-slate-500">
                              Sites rejected by the backend
                              relocation assessment.
                            </p>
                          </div>

                          <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
                            {rejectedSites.length}
                          </span>
                        </div>

                        <div className="mt-5 space-y-4">
                          {rejectedSites.map(
                            (site) => (
                              <div
                                key={site.site_id}
                                className="rounded-lg border border-slate-200 p-4"
                              >
                                <div className="flex items-start justify-between gap-4">
                                  <div>
                                    <h3 className="font-semibold text-slate-900">
                                      {site.site_id}
                                    </h3>

                                    <p className="mt-1 text-sm text-slate-500">
                                      Accessibility:{" "}
                                      {site.accessibility ??
                                        "Not provided"}
                                    </p>
                                  </div>

                                  <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
                                    Rejected
                                  </span>
                                </div>

                                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                                  <div className="rounded-lg bg-slate-50 p-3">
                                    <p className="text-xs text-slate-500">
                                      Safety
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-slate-900">
                                      {site.safety}
                                    </p>
                                  </div>

                                  <div className="rounded-lg bg-slate-50 p-3">
                                    <p className="text-xs text-slate-500">
                                      Capacity
                                    </p>

                                    <p className="mt-1 text-sm font-semibold text-slate-900">
                                      {site.capacity}
                                    </p>
                                  </div>
                                </div>

                                {site.rejection_reason && (
                                  <div className="mt-4 rounded-lg bg-red-50 p-3">
                                    <p className="text-xs font-medium text-red-700">
                                      Rejection Reason
                                    </p>

                                    <p className="mt-1 text-sm text-red-800">
                                      {
                                        site.rejection_reason
                                      }
                                    </p>
                                  </div>
                                )}
                              </div>
                            ),
                          )}

                          {rejectedSites.length ===
                            0 && (
                            <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500">
                              No rejected sites were
                              provided by the backend.
                            </p>
                          )}
                        </div>
                      </div>
                    </section>
                  </>
                )}
            </>
          )}
      </div>
    </DashboardShell>
  );
}
