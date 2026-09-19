import DashboardShell from "@/components/layout/DashboardShell";
import Header from "@/components/layout/Header";
import DashboardContent from "@/components/dashboard/DashboardContent";

export default function HomePage() {
  return (
    <DashboardShell>
      <Header
        title="Dashboard"
        description="Wayanad habitation risk and relocation overview"
      />

      <div className="space-y-8 p-8">
        <DashboardContent />

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Risk Map
          </h2>

          <p className="mt-2 text-sm text-slate-500">
            Interactive habitation risk map will be integrated here.
          </p>
        </section>
      </div>
    </DashboardShell>
  );
}