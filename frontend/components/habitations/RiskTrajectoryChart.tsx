"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface RiskTrajectoryChartProps {
  current: number;
  risk24h: number;
  risk72h: number;
}

export default function RiskTrajectoryChart({
  current,
  risk24h,
  risk72h,
}: RiskTrajectoryChartProps) {
  const data = [
    {
      period: "Current",
      risk: current,
    },
    {
      period: "24h",
      risk: risk24h,
    },
    {
      period: "72h",
      risk: risk72h,
    },
  ];

  return (
    <div>
      <div className="mb-4 grid grid-cols-3 gap-3">
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-500">
            Current
          </p>

          <p className="mt-1 text-xl font-bold text-slate-900">
            {(current * 100).toFixed(0)}%
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-500">
            Next 24h
          </p>

          <p className="mt-1 text-xl font-bold text-slate-900">
            {(risk24h * 100).toFixed(0)}%
          </p>
        </div>

        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-500">
            Next 72h
          </p>

          <p className="mt-1 text-xl font-bold text-slate-900">
            {(risk72h * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={data}
            margin={{
              top: 10,
              right: 20,
              left: 0,
              bottom: 10,
            }}
          >
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="period" />

            <YAxis
              domain={[0, 1]}
              tickFormatter={(value) =>
                `${Math.round(value * 100)}%`
              }
            />

            <Tooltip
              formatter={(value) =>
                typeof value === "number"
                  ? `${(value * 100).toFixed(0)}%`
                  : value
              }
            />

            <Line
              type="monotone"
              dataKey="risk"
              name="Risk"
              strokeWidth={3}
              dot={{ r: 5 }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}