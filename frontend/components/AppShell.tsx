"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "D" },
  { href: "/inbox", label: "Inbox", icon: "I" },
  { href: "/tasks", label: "Tasks", icon: "T" },
  { href: "/alerts", label: "Alerts", icon: "A" }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen lg:flex">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <TopNavbar />
        <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="border-b border-line bg-canvas/88 px-4 py-4 backdrop-blur lg:sticky lg:top-0 lg:h-screen lg:w-72 lg:border-b-0 lg:border-r lg:px-5">
      <div className="flex items-center justify-between lg:block">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600 font-bold text-white shadow-glow">R</div>
          <div>
            <div className="text-sm font-semibold tracking-wide text-white">REPLYNT</div>
            <div className="text-xs text-slate-400">Email intelligence</div>
          </div>
        </Link>
      </div>
      <nav className="mt-5 grid grid-cols-4 gap-2 lg:grid-cols-1">
        {navItems.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-center gap-3 rounded-xl px-3 py-2.5 text-sm transition lg:justify-start ${
                active
                  ? "border border-blue-500/40 bg-blue-500/12 text-blue-100"
                  : "border border-transparent text-slate-400 hover:bg-white/[0.04] hover:text-slate-100"
              }`}
            >
              <span className="grid h-6 w-6 place-items-center rounded-lg bg-white/[0.06] text-xs">{item.icon}</span>
              <span className="hidden lg:inline">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

function TopNavbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-canvas/78 px-4 py-3 backdrop-blur sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-[0.24em] text-blue-300">AI operations</div>
          <h1 className="mt-1 text-xl font-semibold text-white">Command center</h1>
        </div>
        <div className="hidden rounded-xl border border-line bg-panel px-3 py-2 text-sm text-slate-300 sm:block">
          Realtime sync active
        </div>
      </div>
    </header>
  );
}
