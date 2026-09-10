"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, CalendarPlus, CalendarClock, Route, Car, Users, Radar } from "lucide-react";
import type { Role } from "@/lib/types";
import { canApproveBookings } from "@/lib/permissions";

interface Item {
  href: string;
  icon: typeof Home;
  label: string;
}

function itemsForRole(role: Role): Item[] {
  if (role === "EMPLOYEE") {
    return [
      { href: "/dashboard", icon: Home, label: "Home" },
      { href: "/bookings/new", icon: CalendarPlus, label: "Book" },
      { href: "/bookings", icon: CalendarClock, label: "Bookings" },
    ];
  }
  if (role === "DRIVER") {
    return [
      { href: "/dashboard", icon: Home, label: "Home" },
      { href: "/bookings", icon: Route, label: "Trips" },
    ];
  }
  const items: Item[] = [
    { href: "/dashboard", icon: Home, label: "Home" },
    { href: "/admin/vehicles", icon: Car, label: "Fleet" },
    { href: "/admin/live-tracking", icon: Radar, label: "Tracking" },
    { href: "/admin/employees", icon: Users, label: "People" },
  ];
  if (canApproveBookings(role)) items.splice(1, 0, { href: "/bookings", icon: CalendarClock, label: "Bookings" });
  return items.slice(0, 5);
}

export function MobileNav({ role }: { role: Role }) {
  const pathname = usePathname();
  const items = itemsForRole(role);

  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t border-slate-200 bg-white/95 backdrop-blur md:hidden">
      {items.map((item) => {
        const Icon = item.icon;
        const active = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium ${
              active ? "text-indigo-600" : "text-slate-400"
            }`}
          >
            <Icon size={20} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
