"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Role } from "@/lib/types";
import { buildNav, type NavItem } from "@/lib/nav-config";

function NavLink({ item, active }: { item: NavItem; active: boolean }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      className={`group relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all ${
        active
          ? "bg-gradient-to-r from-indigo-500/15 to-violet-500/10 text-indigo-300"
          : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
      }`}
    >
      {active && <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-indigo-400" />}
      <Icon size={18} className={active ? "text-indigo-300" : "text-slate-500 group-hover:text-slate-200"} />
      {item.label}
    </Link>
  );
}

export function Sidebar({ role }: { role: Role }) {
  const pathname = usePathname();
  const sections = buildNav(role);

  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-[#0f1222] p-4 md:flex">
      <div className="mb-6 flex items-center gap-2.5 px-2 pt-1">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-lg font-bold text-white shadow-lg shadow-indigo-900/40">
          F
        </div>
        <div>
          <p className="text-base font-semibold leading-tight text-white">Fleet</p>
          <p className="text-[11px] leading-tight text-slate-500">Management Suite</p>
        </div>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto pb-4">
        {sections.map((section, i) => (
          <div key={i}>
            {section.title && (
              <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-600">{section.title}</p>
            )}
            <div className="flex flex-col gap-0.5">
              {section.items.map((item) => (
                <NavLink key={item.href} item={item} active={pathname === item.href || pathname.startsWith(item.href + "/")} />
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="rounded-xl bg-white/5 px-3 py-2.5 text-[11px] text-slate-500">
        <p className="font-medium text-slate-400">Signed in as</p>
        <p className="mt-0.5 text-slate-500">{role.replaceAll("_", " ")}</p>
      </div>
    </aside>
  );
}
