import StatCard from "@/components/common/StatCard";

interface RiskSummaryProps {
  highPriorityCount: number;
  immediateAssessmentCount: number;
  systemStatus: string;
}

export default function RiskSummary({
  highPriorityCount,
  immediateAssessmentCount,
  systemStatus,
}: RiskSummaryProps) {
  return (
    <section>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">
          Risk & Priority Summary
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Backend-reported priority and system status across monitored habitations.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <StatCard
          label="High-Priority Habitations"
          value={String(highPriorityCount)}
          description="Habitations currently marked high priority by the backend."
          status={
            highPriorityCount > 0
              ? "warning"
              : "normal"
          }
        />

        <StatCard
          label="Immediate Assessments"
          value={String(immediateAssessmentCount)}
          description="Habitations currently requiring immediate assessment."
          status={
            immediateAssessmentCount > 0
              ? "danger"
              : "normal"
          }
        />

        <StatCard
          label="System Status"
          value={systemStatus}
          description="Current availability status reported by the backend."
          status={
            systemStatus.toLowerCase() === "ready"
              ? "normal"
              : "warning"
          }
        />
      </div>
    </section>
  );
}
