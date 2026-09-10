import type { Role } from "@/lib/types";

export const ADMIN_ROLES: Role[] = ["SUPER_ADMIN", "ADMIN"];
export const MANAGER_ROLES: Role[] = ["SUPER_ADMIN", "ADMIN", "TRANSPORT_MANAGER"];

export function isAdmin(role: Role): boolean {
  return ADMIN_ROLES.includes(role);
}

export function canApproveBookings(role: Role): boolean {
  return MANAGER_ROLES.includes(role);
}

export function canManageMasterData(role: Role): boolean {
  return MANAGER_ROLES.includes(role);
}
