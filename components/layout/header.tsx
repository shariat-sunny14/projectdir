import { Search, LogOut } from "lucide-react";
import { logoutAction } from "@/lib/actions/auth-actions";
import { NotificationBell } from "@/components/layout/notification-bell";
import { MobileMenu } from "@/components/layout/mobile-menu";
import type { SessionPayload } from "@/lib/auth/session";

export function Header({ session }: { session: SessionPayload }) {
  const initials = session.fullName
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-2 border-b border-slate-200/70 bg-white/80 px-3 backdrop-blur-md sm:gap-4 sm:px-6">
      <MobileMenu role={session.role} />

      <div className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-transparent bg-slate-100/80 px-3 py-2 transition-colors focus-within:border-indigo-200 focus-within:bg-white focus-within:shadow-sm sm:max-w-md">
        <Search size={16} className="shrink-0 text-slate-400" />
        <input
          placeholder="Search vehicles, bookings, employees..."
          className="w-full min-w-0 bg-transparent text-sm outline-none placeholder:text-slate-400"
        />
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <NotificationBell />

        <div className="hidden items-center gap-2.5 border-l border-slate-200 pl-3 sm:flex">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-sm font-semibold text-white shadow-sm">
            {initials}
          </div>
          <div className="text-sm leading-tight">
            <p className="font-semibold text-slate-800">{session.fullName}</p>
            <p className="text-xs text-slate-400">{session.role.replaceAll("_", " ")}</p>
          </div>
        </div>

        <form action={logoutAction}>
          <button
            type="submit"
            className="flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-sm font-medium text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600"
            title="Log out"
          >
            <LogOut size={16} />
            <span className="hidden md:inline">Logout</span>
          </button>
        </form>
      </div>
    </header>
  );
}
