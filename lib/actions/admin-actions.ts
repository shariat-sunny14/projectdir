"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "@/lib/auth/session";
import { isAdmin } from "@/lib/permissions";
import { approveUser, rejectUser } from "@/lib/services/auth-service";
import { usersRepo } from "@/lib/json-db/repositories";
import { writeAudit } from "@/lib/services/audit-service";
import { createNotification } from "@/lib/services/notification-service";
import type { Role } from "@/lib/types";

async function requireAdmin() {
  const session = await getSession();
  if (!session || !isAdmin(session.role)) {
    throw new Error("Not authorized.");
  }
  return session;
}

export async function approveUserAction(userId: string, role?: Role) {
  const session = await requireAdmin();
  if (role) {
    // BR-002: only an administrator can change a user's role — apply it as part of approval.
    await usersRepo.update(userId, { role });
    await writeAudit(session.userId, "User", "ASSIGN", userId, `Role set to ${role} during approval`);
  }
  await approveUser(userId, session.userId);
  revalidatePath("/admin/user-approvals");
}

export async function rejectUserAction(userId: string, reason: string) {
  const session = await requireAdmin();
  await rejectUser(userId, session.userId, reason || "Not specified");
  revalidatePath("/admin/user-approvals");
}

/** BR-002: only SUPER_ADMIN/ADMIN can change a user's role. */
export async function setUserRoleAction(userId: string, role: Role) {
  const session = await requireAdmin();
  if (userId === session.userId && role !== session.role) {
    throw new Error("You cannot change your own role.");
  }
  const updated = await usersRepo.update(userId, { role });
  if (!updated) throw new Error("User not found.");

  await writeAudit(session.userId, "User", "ASSIGN", userId, `Role changed to ${role}`);
  await createNotification(userId, "Role Updated", `Your role has been changed to ${role.replaceAll("_", " ")}.`, "SYSTEM");

  revalidatePath("/admin/employees");
  revalidatePath("/admin/user-approvals");
}
