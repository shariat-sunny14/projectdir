"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData } from "@/lib/permissions";
import { maintenanceRepo, expensesRepo, vehiclesRepo, bookingsRepo, usersRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { writeAudit } from "@/lib/services/audit-service";
import { overlaps } from "@/lib/services/availability-service";
import { saveUploadedFile } from "@/lib/services/upload-service";
import { createNotification } from "@/lib/services/notification-service";
import { sendEmail } from "@/lib/services/email-service";
import { AppError, runAction, type ActionResult } from "@/lib/errors";

async function requireEntryPermission() {
  const session = await getSession();
  // #19: SUPER_ADMIN/ADMIN/TRANSPORT_MANAGER manage directly; DRIVER can submit entries
  // for approval.
  if (!session || !(canManageMasterData(session.role) || session.role === "DRIVER")) {
    throw new AppError("ERR_FORBIDDEN", "Not authorized.");
  }
  return session;
}

async function requireManager() {
  const session = await getSession();
  if (!session || !canManageMasterData(session.role)) {
    throw new AppError("ERR_FORBIDDEN", "Not authorized.");
  }
  return session;
}

async function notifyManagersOf(title: string, message: string, type: "MAINTENANCE" | "SYSTEM", relatedId?: string) {
  const managers = (await usersRepo.findAll()).filter((u) => canManageMasterData(u.role));
  await Promise.all(managers.map((m) => createNotification(m.id, title, message, type, relatedId)));
}

function num(formData: FormData, key: string): number {
  const v = formData.get(key);
  return v ? Number(v) : 0;
}

/** Phase 18 + Task 19: SUPER_ADMIN/ADMIN/TRANSPORT_MANAGER entries are auto-approved
 * and immediately affect vehicle status. DRIVER entries go in as PENDING and wait for
 * an admin to approve/reject before any vehicle status changes take effect. */
export async function addMaintenanceAction(formData: FormData): Promise<ActionResult<{ conflictWarning: boolean }>> {
  return runAction(async () => {
    const session = await requireEntryPermission();
    const id = await nextId("SRV");
    const now = new Date().toISOString();
    const vehicleId = String(formData.get("vehicleId"));
    const requestedStatus = (String(formData.get("status")) || "OPEN") as "OPEN" | "COMPLETED";
    const serviceDate = String(formData.get("serviceDate"));
    const isDriverSubmission = session.role === "DRIVER";

    const partsCost = num(formData, "partsCost");
    const labourCost = num(formData, "labourCost");
    const otherCost = num(formData, "otherCost");
    const totalCost = partsCost + labourCost + otherCost;

    const documentPath = await saveUploadedFile(formData.get("document") as File | null);

    // Driver submissions stay OPEN/pending until an admin approves them — the vehicle
    // isn't taken out of service on a driver's say-so alone.
    const status = isDriverSubmission ? "OPEN" : requestedStatus;

    await maintenanceRepo.insert({
      id,
      vehicleId,
      serviceDate,
      serviceType: String(formData.get("serviceType")) as never,
      currentKm: formData.get("currentKm") ? Number(formData.get("currentKm")) : undefined,
      workshop: String(formData.get("workshop") || ""),
      mechanic: String(formData.get("mechanic") || ""),
      description: String(formData.get("description") || ""),
      partsCost,
      labourCost,
      otherCost,
      totalCost,
      nextServiceDate: String(formData.get("nextServiceDate") || "") || undefined,
      nextServiceKm: formData.get("nextServiceKm") ? Number(formData.get("nextServiceKm")) : undefined,
      invoiceNumber: String(formData.get("invoiceNumber") || ""),
      remarks: String(formData.get("remarks") || ""),
      status,
      submittedByUserId: session.userId,
      approvalStatus: isDriverSubmission ? "PENDING" : "APPROVED",
      documentPath,
      createdAt: now,
      updatedAt: now,
    });

    let conflictWarning = false;

    if (!isDriverSubmission && status === "OPEN") {
      await vehiclesRepo.update(vehicleId, { status: "MAINTENANCE" });

      // Phase 18: warn admin if an existing approved booking overlaps "now" for this vehicle —
      // do NOT silently auto-cancel; admin resolves manually.
      const bookings = await bookingsRepo.findAll();
      const nowIso = new Date().toISOString();
      const inOneDay = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
      conflictWarning = bookings.some(
        (b) =>
          b.assignedVehicleId === vehicleId &&
          ["APPROVED", "ON_TRIP"].includes(b.status) &&
          overlaps(b.startDateTime, b.endDateTime, nowIso, inOneDay)
      );
    }

    await writeAudit(
      session.userId,
      "Maintenance",
      "CREATE",
      id,
      `Vehicle ${vehicleId}${isDriverSubmission ? " — submitted by driver, pending approval" : ""}${conflictWarning ? " — booking conflict warning" : ""}`
    );

    if (isDriverSubmission) {
      const vehicle = await vehiclesRepo.findById(vehicleId);
      await notifyManagersOf(
        "Maintenance Entry Submitted",
        `A driver submitted a maintenance entry for ${vehicle?.registrationNumber ?? vehicleId} awaiting your approval.`,
        "MAINTENANCE",
        id
      );
    }

    revalidatePath("/maintenance");
    return { conflictWarning };
  });
}

/** Admin approves a driver-submitted maintenance entry — only now do the Phase 18 side
 * effects (vehicle -> MAINTENANCE if OPEN) actually apply. */
export async function approveMaintenanceEntryAction(id: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireManager();
    const record = await maintenanceRepo.update(id, { approvalStatus: "APPROVED" });
    if (!record) throw new AppError("ERR_NOT_FOUND", "Service record not found.");

    if (record.status === "OPEN") {
      await vehiclesRepo.update(record.vehicleId, { status: "MAINTENANCE" });
    }

    await writeAudit(session.userId, "Maintenance", "APPROVE", id);
    if (record.submittedByUserId) {
      await createNotification(record.submittedByUserId, "Maintenance Entry Approved", `Your maintenance entry ${id} was approved.`, "MAINTENANCE", id);
      const submitter = await usersRepo.findById(record.submittedByUserId);
      if (submitter) {
        await sendEmail(submitter.email, "MAINTENANCE_APPROVED", `Maintenance entry ${id} approved`, `Hi ${submitter.fullName}, your maintenance entry ${id} has been approved.`);
      }
    }
    revalidatePath("/maintenance");
    return null;
  });
}

export async function rejectMaintenanceEntryAction(id: string, reason: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireManager();
    const record = await maintenanceRepo.update(id, { approvalStatus: "REJECTED", approvalRejectionReason: reason });
    if (!record) throw new AppError("ERR_NOT_FOUND", "Service record not found.");

    await writeAudit(session.userId, "Maintenance", "REJECT", id, reason);
    if (record.submittedByUserId) {
      await createNotification(record.submittedByUserId, "Maintenance Entry Rejected", `Your maintenance entry ${id} was rejected: ${reason}`, "MAINTENANCE", id);
      const submitter = await usersRepo.findById(record.submittedByUserId);
      if (submitter) {
        await sendEmail(submitter.email, "MAINTENANCE_REJECTED", `Maintenance entry ${id} rejected`, `Hi ${submitter.fullName}, your maintenance entry ${id} was rejected.\nReason: ${reason}`);
      }
    }
    revalidatePath("/maintenance");
    return null;
  });
}

/** Phase 18: closing an OPEN, approved service record returns the vehicle to AVAILABLE. */
export async function completeMaintenanceAction(id: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireManager();
    const record = await maintenanceRepo.update(id, { status: "COMPLETED" });
    if (!record) throw new AppError("ERR_NOT_FOUND", "Service record not found.");
    if (record.approvalStatus === "APPROVED") {
      await vehiclesRepo.update(record.vehicleId, { status: "AVAILABLE" });
    }
    await writeAudit(session.userId, "Maintenance", "UPDATE", id, "Marked completed");
    revalidatePath("/maintenance");
    return null;
  });
}

/** Phase 19/20 + Task 19: toll, tip and parking are just Expense records with the
 * matching category. Driver-submitted expenses go in PENDING for admin approval;
 * admin/manager entries are auto-approved. */
export async function addExpenseAction(formData: FormData): Promise<ActionResult<{ id: string }>> {
  return runAction(async () => {
    const session = await requireEntryPermission();
    const id = await nextId("EXP");
    const now = new Date().toISOString();
    const isDriverSubmission = session.role === "DRIVER";

    const documentPath = await saveUploadedFile(formData.get("document") as File | null);

    await expensesRepo.insert({
      id,
      vehicleId: String(formData.get("vehicleId")),
      bookingId: String(formData.get("bookingId") || "") || undefined,
      expenseDate: String(formData.get("expenseDate")),
      category: String(formData.get("category")) as never,
      location: String(formData.get("location") || ""),
      amount: Number(formData.get("amount")),
      paymentMethod: String(formData.get("paymentMethod")) as never,
      description: String(formData.get("description") || ""),
      createdByUserId: session.userId,
      approvalStatus: isDriverSubmission ? "PENDING" : "APPROVED",
      documentPath,
      createdAt: now,
      updatedAt: now,
    });

    await writeAudit(session.userId, "Expense", "CREATE", id, isDriverSubmission ? "Submitted by driver, pending approval" : undefined);

    if (isDriverSubmission) {
      await notifyManagersOf("Expense Entry Submitted", `A driver submitted an expense entry (${id}) awaiting your approval.`, "SYSTEM", id);
    }

    revalidatePath("/expenses");
    return { id };
  });
}

export async function approveExpenseEntryAction(id: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireManager();
    const record = await expensesRepo.update(id, { approvalStatus: "APPROVED" });
    if (!record) throw new AppError("ERR_NOT_FOUND", "Expense not found.");

    await writeAudit(session.userId, "Expense", "APPROVE", id);
    await createNotification(record.createdByUserId, "Expense Approved", `Your expense entry ${id} was approved.`, "SYSTEM", id);
    const submitter = await usersRepo.findById(record.createdByUserId);
    if (submitter) {
      await sendEmail(submitter.email, "EXPENSE_APPROVED", `Expense ${id} approved`, `Hi ${submitter.fullName}, your expense entry ${id} has been approved.`);
    }
    revalidatePath("/expenses");
    return null;
  });
}

export async function rejectExpenseEntryAction(id: string, reason: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireManager();
    const record = await expensesRepo.update(id, { approvalStatus: "REJECTED", approvalRejectionReason: reason });
    if (!record) throw new AppError("ERR_NOT_FOUND", "Expense not found.");

    await writeAudit(session.userId, "Expense", "REJECT", id, reason);
    await createNotification(record.createdByUserId, "Expense Rejected", `Your expense entry ${id} was rejected: ${reason}`, "SYSTEM", id);
    const submitter = await usersRepo.findById(record.createdByUserId);
    if (submitter) {
      await sendEmail(submitter.email, "EXPENSE_REJECTED", `Expense ${id} rejected`, `Hi ${submitter.fullName}, your expense entry ${id} was rejected.\nReason: ${reason}`);
    }
    revalidatePath("/expenses");
    return null;
  });
}

export async function deleteExpenseAction(id: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireManager();
    const removed = await expensesRepo.remove(id);
    if (!removed) throw new AppError("ERR_NOT_FOUND", "Expense not found.");
    await writeAudit(session.userId, "Expense", "DELETE", id);
    revalidatePath("/expenses");
    return null;
  });
}
