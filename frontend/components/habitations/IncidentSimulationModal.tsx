"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import type { SimulationResult } from "@/types/api";

interface IncidentSimulationModalProps {
  habitationId: string;
  habitationName: string;
  isOpen: boolean;
  onClose: () => void;
}

export default function IncidentSimulationModal({
  habitationId,
  habitationName,
  isOpen,
  onClose,
}: IncidentSimulationModalProps) {
  const [rainfallMm, setRainfallMm] = useState<number>(180);
  const [horizon, setHorizon] = useState<string>("24h");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);

  if (!isOpen) return null;

  async function handleRunSimulation() {
    try {
      setLoading(true);
      setError(null);
      const res = await api.simulateHabitationIncident(habitationId, rainfallMm, horizon);
      setSimulationResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Incident simulation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-3xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 bg-slate-900 px-6 py-4 text-white">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded bg-amber-500 px-2 py-0.5 text-[11px] font-bold tracking-wide text-slate-950 uppercase">
                WHAT-IF SIMULATION
              </span>
              <h2 className="text-lg font-bold">Rainfall Incident Simulation</h2>
            </div>
            <p className="mt-0.5 text-xs text-slate-300">
              Target Habitation: <strong className="text-white">{habitationName}</strong> ({habitationId})
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[80vh] overflow-y-auto">
          {/* Simulation Input Controls */}
          <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-5 space-y-4">
            <div className="flex items-start gap-3">
              <span className="text-amber-600 text-lg font-bold">⚡</span>
              <div>
                <h3 className="text-sm font-semibold text-amber-900">
                  Simulate Heavy Rainfall Event
                </h3>
                <p className="text-xs text-amber-800 mt-0.5">
                  Test how custom cloudburst or heavy monsoon rainfall affects spatial landslide risk through Model A.
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-slate-700">
                  Simulated Rainfall (mm)
                </label>
                <div className="mt-1 flex items-center gap-2">
                  <input
                    type="number"
                    min="0"
                    max="500"
                    value={rainfallMm}
                    onChange={(e) => setRainfallMm(parseFloat(e.target.value) || 0)}
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-bold text-slate-900 shadow-sm focus:border-amber-500 focus:outline-none"
                  />
                  <span className="text-xs font-semibold text-slate-500">mm</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700">
                  Forecast Horizon Window
                </label>
                <select
                  value={horizon}
                  onChange={(e) => setHorizon(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-900 shadow-sm focus:border-amber-500 focus:outline-none"
                >
                  <option value="24h">Next 24 Hours (+24h)</option>
                  <option value="72h">Next 72 Hours (+72h)</option>
                </select>
              </div>
            </div>

            <button
              type="button"
              onClick={handleRunSimulation}
              disabled={loading}
              className="w-full rounded-xl bg-amber-600 py-3 text-sm font-bold text-white shadow-md transition hover:bg-amber-700 disabled:opacity-50"
            >
              {loading ? "Executing Model A Simulation..." : "⚡ RUN INCIDENT SIMULATION"}
            </button>
          </div>

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-800">
              {error}
            </div>
          )}

          {/* Side-by-Side Comparison */}
          {simulationResult && (
            <div className="space-y-4 animate-fadeIn">
              <div className="rounded-lg border border-amber-300 bg-amber-100 p-3 text-center text-xs font-bold text-amber-900 uppercase tracking-wide">
                ⚠️ SIMULATION — NOT OBSERVED DATA
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {/* REAL CONDITIONS */}
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                    <span className="text-xs font-semibold text-slate-500 uppercase">
                      REAL OBSERVED / FORECAST
                    </span>
                    <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800">
                      BASELINE
                    </span>
                  </div>

                  <div>
                    <p className="text-xs text-slate-500">Current Risk</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {(simulationResult.baseline.current_risk * 100).toFixed(0)}%
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-slate-500">24h Forecast Risk</p>
                      <p className="font-semibold text-slate-800">
                        {(simulationResult.baseline.risk_24h * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">72h Forecast Risk</p>
                      <p className="font-semibold text-slate-800">
                        {(simulationResult.baseline.risk_72h * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-100 text-xs flex justify-between">
                    <span className="text-slate-500">Trajectory:</span>
                    <span className="font-semibold text-slate-900">
                      {simulationResult.baseline.trajectory}
                    </span>
                  </div>
                </div>

                {/* SIMULATED INCIDENT */}
                <div className="rounded-xl border border-amber-300 bg-amber-50/50 p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between border-b border-amber-200 pb-2">
                    <span className="text-xs font-bold text-amber-900 uppercase">
                      SIMULATED INCIDENT ({simulationResult.simulated_rainfall_mm} mm)
                    </span>
                    <span className="rounded bg-amber-500 px-2 py-0.5 text-[10px] font-bold text-slate-950">
                      SIMULATED
                    </span>
                  </div>

                  <div>
                    <p className="text-xs text-amber-800 font-medium">Simulated Risk</p>
                    <p className="text-2xl font-bold text-amber-900">
                      {(simulationResult.simulation_result.current_risk * 100).toFixed(0)}%
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <p className="text-amber-800">Simulated 24h Risk</p>
                      <p className="font-bold text-amber-900">
                        {(simulationResult.simulation_result.risk_24h * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-amber-800">Simulated 72h Risk</p>
                      <p className="font-bold text-amber-900">
                        {(simulationResult.simulation_result.risk_72h * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-amber-200 text-xs flex justify-between">
                    <span className="text-amber-800">Simulated Trajectory:</span>
                    <span className="font-bold text-red-700">
                      {simulationResult.simulation_result.trajectory}
                    </span>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 space-y-2">
                <p className="text-xs font-semibold text-slate-700 uppercase">
                  Simulation Risk Drivers
                </p>
                <ul className="space-y-1 text-xs text-slate-600">
                  {simulationResult.simulation_result.drivers.map((driver) => (
                    <li key={driver} className="flex items-center gap-2">
                      <span className="text-amber-600">•</span>
                      <span>{driver}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
