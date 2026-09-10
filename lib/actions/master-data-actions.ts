"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData, isAdmin } from "@/lib/permissions";
import { departmentSchema, vehicleSchema, driverSchema } from "@/lib/validators/master-data";
import { departmentsRepo, vehiclesRepo, driversRepo, usersRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { writeAudit } from "@/lib/services/audit-service";

async function requireManager() {
  const session = await getSession();
  if (!session || !canManageMasterData(session.role)) {
    throw new Error("Not authorized.");
  }
  return session;
}

function toObj(formData: FormData) {
  return Object.fromEntries(formData.entries());
}

// ---- Department -----------------------------------------------------------

export async function saveDepartmentAction(formData: FormData) {
  const session = await requireManager();
  const raw = toObj(formData);
  const parsed = departmentSchema.parse(raw);
  const id = String(raw.id || "");
  const now = new Date().toISOString();

  if (id) {
    await departmentsRepo.update(id, parsed);
    await writeAudit(session.userId, "Department", "UPDATE", id);
  } else {
    const newId = await nextId("DEP");
    await departmentsRepo.insert({ id: newId, ...parsed, createdAt: now, updatedAt: now });
    await writeAudit(session.userId, "Department", "CREATE", newId);
  }
  revalidatePath("/admin/departments");
}

export async function setDepartmentStatusAction(id: string, status: "ACTIVE" | "INACTIVE") {
  const session = await requireManager();
  await departmentsRepo.update(id, { status });
  await writeAudit(session.userId, "Department", "UPDATE", id, `Status changed to ${status}`);
  revalidatePath("/admin/departments");
}

// ---- Vehicle ----------------------------------------------------------------

export async function saveVehicleAction(formData: FormData) {
  const session = await requireManager();
  const raw = toObj(formData);
  const parsed = vehicleSchema.parse(raw);
  const id = String(raw.id || "");
  const now = new Date().toISOString();

  if (id) {
    await vehiclesRepo.update(id, parsed);
    await writeAudit(session.userId, "Vehicle", "UPDATE", id);
  } else {
    const newId = await nextId("VEH");
    await vehiclesRepo.insert({ id: newId, ...parsed, createdAt: now, updatedAt: now });
    await writeAudit(session.userId, "Vehicle", "CREATE", newId);
  }
  revalidatePath("/admin/vehicles");
}

export async function setVehicleStatusAction(id: string, status: string) {
  const session = await requireManager();
  await vehiclesRepo.update(id, { status: status as never });
  await writeAudit(session.userId, "Vehicle", "UPDATE", id, `Status changed to ${status}`);
  revalidatePath("/admin/vehicles");
}

// ---- Driver -------------------------------------------------------------

export async function saveDriverAction(formData: FormData) {
  const session = await requireManager();
  const raw = toObj(formData);
  const parsed = driverSchema.parse(raw);
  const id = String(raw.id || "");
  const now = new Date().toISOString();

  if (id) {
    await driversRepo.update(id, parsed);
    await writeAudit(session.userId, "Driver", "UPDATE", id);
  } else {
    const newId = await nextId("DRV");
    await driversRepo.insert({ id: newId, ...parsed, createdAt: now, updatedAt: now });
    await writeAudit(session.userId, "Driver", "CREATE", newId);
  }
  revalidatePath("/admin/drivers");
}

export async function setDriverStatusAction(id: string, status: string) {
  const session = await requireManager();
  await driversRepo.update(id, { status: status as never });
  await writeAudit(session.userId, "Driver", "UPDATE", id, `Status changed to ${status}`);
  revalidatePath("/admin/drivers");
}

// ---- Employee (status + profile changes; creation happens via signup) --------

export async function setEmployeeStatusAction(id: string, status: "ACTIVE" | "SUSPENDED") {
  const session = await requireManager();
  await usersRepo.update(id, { status });
  await writeAudit(session.userId, "User", "UPDATE", id, `Status changed to ${status}`);
  revalidatePath("/admin/employees");
}

export async function updateEmployeeAction(formData: FormData) {
  const session = await requireManager();
  const id = String(formData.get("id"));

  const patch: Record<string, unknown> = {
    fullName: String(formData.get("fullName") || ""),
    email: String(formData.get("email") || ""),
    phone: String(formData.get("phone") || ""),
    employeeId: String(formData.get("employeeId") || "") || undefined,
    departmentId: String(formData.get("departmentId") || "") || undefined,
    designation: String(formData.get("designation") || ""),
    address: String(formData.get("address") || "") || undefined,
  };

  if (patch.email) {
    const existing = await usersRepo.findOne((u) => u.email.toLowerCase() === String(patch.email).toLowerCase() && u.id !== id);
    if (existing) throw new Error("Another account already uses this email.");
  }

  // Only SUPER_ADMIN/ADMIN may change role (BR-002) or status here — TRANSPORT_MANAGER
  // can still edit the other profile fields above.
  const role = String(formData.get("role") || "");
  const status = String(formData.get("status") || "");
  if (id === session.userId && (role || status)) {
    throw new Error("You cannot change your own role or status.");
  }
  if (role && isAdmin(session.role)) {
    patch.role = role;
  }
  if (status && isAdmin(session.role) && (status === "ACTIVE" || status === "SUSPENDED")) {
    patch.status = status;
  }

  const updated = await usersRepo.update(id, patch);
  if (!updated) throw new Error("Employee not found.");

  await writeAudit(session.userId, "User", "UPDATE", id, "Profile updated");
  revalidatePath("/admin/employees");
}

/** #15: let an admin/manager manually create an employee account directly — already
 * ACTIVE, skipping the self-signup approval queue. */
export async function createEmployeeAction(formData: FormData) {
  const session = await requireManager();

  const email = String(formData.get("email") || "").trim();
  const existing = await usersRepo.findOne((u) => u.email.toLowerCase() === email.toLowerCase());
  if (existing) throw new Error("An account with this email already exists.");

  const role = String(formData.get("role") || "EMPLOYEE");
  if ((role === "ADMIN" || role === "SUPER_ADMIN" || role === "TRANSPORT_MANAGER") && !isAdmin(session.role)) {
    throw new Error("Only Super Admin / Admin can create accounts with that role.");
  }

  const { hashPassword } = await import("@/lib/auth/password");
  const passwordHash = await hashPassword(String(formData.get("password") || "Passw0rd!"));

  const id = await nextId("USR");
  const now = new Date().toISOString();
  await usersRepo.insert({
    id,
    fullName: String(formData.get("fullName") || ""),
    email,
    phone: String(formData.get("phone") || ""),
    employeeId: String(formData.get("employeeId") || "") || undefined,
    departmentId: String(formData.get("departmentId") || "") || undefined,
    designation: String(formData.get("designation") || ""),
    passwordHash,
    role: role as never,
    status: "ACTIVE",
    createdAt: now,
    updatedAt: now,
  });

  await writeAudit(session.userId, "User", "CREATE", id, `Manually created (${role})`);
  revalidatePath("/admin/employees");
}
