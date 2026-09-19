import type { ReactNode } from "react";

import Sidebar from "./Sidebar";

interface DashboardShellProps {
  children: ReactNode;
}

export default function DashboardShell({
  children,
}: DashboardShellProps) {
  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar />

      <main className="min-w-0 flex-1">
        {children}
      </main>
    </div>
  );
}

