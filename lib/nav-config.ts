import {
  LayoutDashboard,
  Car,
  Users,
  CalendarClock,
  CalendarPlus,
  Wrench,
  Wallet,
  Building2,
  BarChart3,
  ShieldCheck,
  UserCheck,
  Mail,
  FileClock,
  Route,
  Radar,
} from "lucide-react";
import type { Role } from "@/lib/types";
import { isAdmin, canApproveBookings } from "@/lib/permissions";

export type IconType = typeof Car;

export interface NavItem {
  href: string;
  icon: IconType;
  label: string;
}

export interface NavSection {
  title?: string;
  items: NavItem[];
}

/**
 * Single source of truth for the app navigation.
 * Used by both the desktop Sidebar and the mobile drawer (MobileMenu),
 * so any role/permission change only needs to happen here.
 */
export function buildNav(role: Role): NavSection[] {
  const sections: NavSection[] = [{ items: [{ href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" }] }];

  if (role === "EMPLOYEE") {
    sections.push({
      title: "Bookings",
      items: [
        { href: "/bookings/new", icon: CalendarPlus, label: "New Booking" },
        { href: "/bookings", icon: CalendarClock, label: "My Bookings" },
      ],
    });
    return sections;
  }

  if (role === "DRIVER") {
    sections.push({
      title: "Trips",
      items: [{ href: "/bookings", icon: Route, label: "My Trips" }],
    });
    sections.push({
      title: "Entries",
      items: [
        { href: "/maintenance", icon: Wrench, label: "Maintenance" },
        { href: "/expenses", icon: Wallet, label: "Expenses" },
      ],
    });
    return sections;
  }

  // SUPER_ADMIN / ADMIN / TRANSPORT_MANAGER get the full operational menu.
  sections.push({
    title: "Fleet",
    items: [
      { href: "/admin/vehicles", icon: Car, label: "Vehicles" },
      { href: "/admin/drivers", icon: Users, label: "Drivers" },
      { href: "/admin/live-tracking", icon: Radar, label: "Live Tracking" },
    ],
  });

  if (canApproveBookings(role)) {
    sections.push({
      title: "Bookings",
      items: [
        { href: "/bookings", icon: CalendarClock, label: "All Bookings" },
        { href: "/bookings/new", icon: CalendarPlus, label: "New Booking" },
      ],
    });
  }

  sections.push({
    title: "Operations",
    items: [
      { href: "/maintenance", icon: Wrench, label: "Maintenance" },
      { href: "/expenses", icon: Wallet, label: "Expenses" },
    ],
  });

  sections.push({
    title: "People",
    items: [
      { href: "/admin/employees", icon: Users, label: "Employees" },
      { href: "/admin/departments", icon: Building2, label: "Departments" },
    ],
  });

  sections.push({ title: "Reports", items: [{ href: "/reports", icon: BarChart3, label: "Reports" }] });

  if (isAdmin(role)) {
    sections.push({
      title: "Administration",
      items: [
        { href: "/admin/user-approvals", icon: UserCheck, label: "User Approvals" },
        { href: "/admin/email-logs", icon: Mail, label: "Email Logs" },
        { href: "/admin/audit-logs", icon: FileClock, label: "Audit Logs" },
      ],
    });
  } else {
    sections.push({
      title: "Administration",
      items: [{ href: "/admin/user-approvals", icon: ShieldCheck, label: "Booking Approvals" }],
    });
  }

  return sections;
}
