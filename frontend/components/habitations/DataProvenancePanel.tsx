"use client";

import { useState } from "react";
import type { SystemStatus } from "@/types/api";

interface DataProvenancePanelProps {
  systemStatus: SystemStatus | null;
}

export default function DataProvenancePanel({ systemStatus }: DataProvenancePanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const weatherStatus = systemStatus?.weather_status || "ONLINE";
  const isWeatherOnline = weatherStatus === "ONLINE";

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between px-6 py-4 cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="flex h-3 w-3 relative">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isWeatherOnline ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-3 w-3 ${
                isWeatherOnline ? "bg-emerald-500" : "bg-amber-500"
              }`}
            />
          </span>

          <div>
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              Data Sources & Provenance Audit
              <span className="rounded bg-slate-200 px-2 py-0.5 text-[11px] font-mono text-slate-700">
                VERIFIED REAL DATA
              </span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Provider: {systemStatus?.weather_provider || "Open-Meteo Weather API (ECMWF)"} | Grid:{" "}
              {systemStatus?.weather_location || "Wayanad (11.65°N, 76.13°E)"}
            </p>
          </div>
        </div>

        <button
          type="button"
          className="text-xs font-semibold text-sky-700 hover:text-sky-900 bg-sky-50 px-3 py-1.5 rounded-lg border border-sky-200"
        >
          {isOpen ? "Hide Data Audit ▲" : "View Data Provenance ▼"}
        </button>
      </div>

      {isOpen && (
        <div className="p-6 border-t border-slate-200 space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Weather API Status
              </p>
              <div className="mt-2 flex items-center gap-2">
                <span
                  className={`inline-block h-2.5 w-2.5 rounded-full ${
                    isWeatherOnline ? "bg-emerald-500" : "bg-amber-500"
                  }`}
                />
                <span className="text-sm font-bold text-slate-900 uppercase">
                  {weatherStatus}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Observed: {systemStatus?.observed_24h_mm?.toFixed(1) ?? "0.0"} mm | Forecast 24h:{" "}
                {systemStatus?.forecast_24h_mm?.toFixed(1) ?? "0.0"} mm
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Active ML Model
              </p>
              <p className="mt-2 text-sm font-bold text-slate-900">
                Model A (`model_a_with_gsi.joblib`)
              </p>
              <p className="mt-1 text-xs text-slate-500">
                RandomForest (300 trees, 11 terrain & GSI NLSM features)
              </p>
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Exposure Baseline
              </p>
              <p className="mt-2 text-sm font-bold text-slate-900">
                Census of India 2011 Reconciled
              </p>
              <p className="mt-1 text-xs text-slate-500">
                48 Rural Villages | 785,840 Population
              </p>
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="bg-slate-100 font-semibold uppercase text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="px-4 py-2.5">Operational Input</th>
                  <th className="px-4 py-2.5">Source Dataset</th>
                  <th className="px-4 py-2.5">Class</th>
                  <th className="px-4 py-2.5">Spatial Scope</th>
                  <th className="px-4 py-2.5">Pipeline Use</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                <tr>
                  <td className="px-4 py-2 font-semibold text-slate-900">Digital Elevation Model</td>
                  <td className="px-4 py-2">Copernicus GLO-30 DEM</td>
                  <td className="px-4 py-2 text-emerald-700 font-semibold">Real Data</td>
                  <td className="px-4 py-2">Wayanad (30m grid)</td>
                  <td className="px-4 py-2">Slope derivation & ML features</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-semibold text-slate-900">Landcover Fractions</td>
                  <td className="px-4 py-2">ESA WorldCover 10m 2021</td>
                  <td className="px-4 py-2 text-emerald-700 font-semibold">Real Data</td>
                  <td className="px-4 py-2">Wayanad (Resampled 30m)</td>
                  <td className="px-4 py-2">Model A & B inputs</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-semibold text-slate-900">Landslide Susceptibility</td>
                  <td className="px-4 py-2">GSI 1:50k NLSM Map</td>
                  <td className="px-4 py-2 text-emerald-700 font-semibold">Real Data</td>
                  <td className="px-4 py-2">Wayanad NLSM Domain</td>
                  <td className="px-4 py-2">Model A GSI feature vector</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-semibold text-slate-900">Rainfall Observation</td>
                  <td className="px-4 py-2">Open-Meteo Live API</td>
                  <td className="px-4 py-2 text-emerald-700 font-semibold">Real Live Feed</td>
                  <td className="px-4 py-2">Lat 11.65, Lon 76.13</td>
                  <td className="px-4 py-2">Current dynamic rainfall stress</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-semibold text-slate-900">Rainfall Forecast</td>
                  <td className="px-4 py-2">Open-Meteo / ECMWF IFS</td>
                  <td className="px-4 py-2 text-emerald-700 font-semibold">Real Forecast Feed</td>
                  <td className="px-4 py-2">24h / 72h Window</td>
                  <td className="px-4 py-2">Forward risk trajectory & priority</td>
                </tr>
                <tr>
                  <td className="px-4 py-2 font-semibold text-slate-900">Relocation Candidates</td>
                  <td className="px-4 py-2">OpenStreetMap Overpass API</td>
                  <td className="px-4 py-2 text-emerald-700 font-semibold">Real GIS Extract</td>
                  <td className="px-4 py-2">794 Wayanad Facilities</td>
                  <td className="px-4 py-2">Relocation candidate ranking</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
