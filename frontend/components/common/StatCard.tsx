interface StatCardProps {
  label: string;
  value: string;
  description: string;
  status?: "normal" | "warning" | "danger";
}

const statusStyles = {
  normal: {
    badge: "bg-emerald-50 text-emerald-700",
    dot: "bg-emerald-500",
  },
  warning: {
    badge: "bg-amber-50 text-amber-700",
    dot: "bg-amber-500",
  },
  danger: {
    badge: "bg-red-50 text-red-700",
    dot: "bg-red-500",
  },
};

const statusLabels = {
  normal: "Normal",
  warning: "Monitor",
  danger: "Attention",
};

export default function StatCard({
  label,
  value,
  description,
  status = "normal",
}: StatCardProps) {
  const styles = statusStyles[status];

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-500">
            {label}
          </p>

          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
            {value}
          </p>
        </div>

        <span
          className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${styles.badge}`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${styles.dot}`}
          />

          {statusLabels[status]}
        </span>
      </div>

      <div className="mt-4 border-t border-slate-100 pt-3">
        <p className="text-xs leading-5 text-slate-500">
          {description}
        </p>
      </div>
    </div>
  );
}