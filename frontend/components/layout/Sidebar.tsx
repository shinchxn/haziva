"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { name: "Dashboard", href: "/", icon: "▦" },
  { name: "Map", href: "/map", icon: "⌖" },
  { name: "Habitations", href: "/habitations", icon: "⌂" },
  { name: "Relocation", href: "/relocation", icon: "⇄" },
  { name: "System Status", href: "/system", icon: "●" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-5">
        <div className="text-2xl font-bold tracking-tight text-slate-900">
          Haziva
        </div>

        <p className="mt-1 text-xs text-slate-500">
          Risk & Relocation Intelligence
        </p>
      </div>

      <nav className="flex-1 space-y-1 p-4">
        {navigation.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href ||
                pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={`${item.name}-${item.href}`}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition ${
                isActive
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
              }`}
            >
              <span className="w-5 text-center">
                {item.icon}
              </span>

              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-slate-200 p-4">
        <div className="rounded-lg bg-slate-50 p-3">
          <p className="text-xs font-medium text-slate-700">
            Decision Support
          </p>

          <p className="mt-1 text-xs leading-5 text-slate-500">
            AI predicts and prioritizes. Authorities verify and decide.
          </p>
        </div>
      </div>
    </aside>
  );
}