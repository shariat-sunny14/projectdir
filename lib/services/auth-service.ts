import { usersRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { hashPassword, verifyPassword } from "@/lib/auth/password";
import { sendEmail } from "@/lib/services/email-service";
import { writeAudit } from "@/lib/services/audit-service";
import { createNotification } from "@/lib/services/notification-service";
import type { SignupInput } from "@/lib/validators/auth";
import type { User } from "@/lib/types";

export async function registerEmployee(input: SignupInput) {
  const existing = await usersRepo.findOne((u) => u.email.toLowerCase() === input.email.toLowerCase());
  if (existing) {
    throw new Error("An account with this email already exists.");
  }

  const id = await nextId("USR");
  const now = new Date().toISOString();
  const passwordHash = await hashPassword(input.password);

  const user: User = {
    id,
    fullName: input.fullName,
    email: input.email,
    phone: input.phone,
    employeeId: input.employeeId,
    departmentId: input.departmentId,
    designation: input.designation,
    passwordHash,
    role: "EMPLOYEE",
    status: "PENDING",
    address: input.address,
    createdAt: now,
    updatedAt: now,
  };

  await usersRepo.insert(user);
  await sendEmail(user.email, "REGISTRATION_SUBMITTED", "Registration received", `Hi ${user.fullName}, your registration is pending admin approval.`);
  await writeAudit(user.id, "User", "CREATE", user.id, "Self-registration submitted");

  return user;
}

export async function authenticate(email: string, password: string) {
  const user = await usersRepo.findOne((u) => u.email.toLowerCase() === email.toLowerCase());
  if (!user) throw new Error("Invalid email or password.");

  const ok = await verifyPassword(password, user.passwordHash);
  if (!ok) throw new Error("Invalid email or password.");

  return user;
}

export async function approveUser(userId: string, actorId: string) {
  const user = await usersRepo.update(userId, { status: "ACTIVE" });
  if (!user) throw new Error("User not found.");
  await sendEmail(user.email, "ACCOUNT_APPROVED", "Account approved", `Hi ${user.fullName}, your account has been approved. You can now log in.`);
  await createNotification(user.id, "Account Approved", "Your account has been approved. You can now log in.", "USER_APPROVAL");
  await writeAudit(actorId, "User", "APPROVE", user.id, `Approved user ${user.email}`);
  return user;
}

export async function rejectUser(userId: string, actorId: string, reason: string) {
  const user = await usersRepo.update(userId, { status: "REJECTED", rejectionReason: reason });
  if (!user) throw new Error("User not found.");
  await sendEmail(user.email, "ACCOUNT_REJECTED", "Account rejected", `Hi ${user.fullName}, your registration was rejected. Reason: ${reason}`);
  await createNotification(user.id, "Account Rejected", `Your registration was rejected. Reason: ${reason}`, "USER_APPROVAL");
  await writeAudit(actorId, "User", "REJECT", user.id, `Rejected user ${user.email}: ${reason}`);
  return user;
}
