import crypto from "crypto";
import { usersRepo, passwordResetOtpsRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { hashPassword } from "@/lib/auth/password";
import { sendEmail } from "@/lib/services/email-service";
import { writeAudit } from "@/lib/services/audit-service";
import { createNotification } from "@/lib/services/notification-service";
import { AppError } from "@/lib/errors";
import type { PasswordResetOtp } from "@/lib/types";

const OTP_TTL_MS = 5 * 60 * 1000; // 5 minutes, per requirement #5
const MAX_ATTEMPTS = 5; // requirement #15: cap wrong attempts, then force a resend
const RESEND_COOLDOWN_MS = 30 * 1000;
const TICKET_TTL_MS = 10 * 60 * 1000; // window to set a new password after a successful OTP verify

const SECRET = process.env.SESSION_SECRET || "dev-secret-change-me";

function sign(data: string): string {
  return crypto.createHmac("sha256", SECRET).update(data).digest("hex");
}

function generateOtp(): string {
  return String(crypto.randomInt(0, 1_000_000)).padStart(6, "0");
}

function hashOtp(otp: string): string {
  return crypto.createHash("sha256").update(`${otp}:${SECRET}`).digest("hex");
}

interface ResetTicketPayload {
  otpId: string;
  userId: string;
  exp: number;
}

function issueResetTicket(payload: ResetTicketPayload): string {
  const json = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${json}.${sign(json)}`;
}

function readResetTicket(ticket: string): ResetTicketPayload {
  const [json, sig] = (ticket || "").split(".");
  if (!json || !sig || sign(json) !== sig) {
    throw new AppError("ERR_VALIDATION", "This session has expired. Please verify your code again.");
  }
  let payload: ResetTicketPayload;
  try {
    payload = JSON.parse(Buffer.from(json, "base64url").toString("utf-8"));
  } catch {
    throw new AppError("ERR_VALIDATION", "This session has expired. Please verify your code again.");
  }
  if (payload.exp < Date.now()) {
    throw new AppError("ERR_VALIDATION", "This session has expired. Please verify your code again.");
  }
  return payload;
}

/** Requirements #2-4 & #10: generate a 6-digit OTP, email it, and (silently)
 * do nothing for unknown/inactive emails so the flow never reveals whether an
 * account exists. Also serves as the "resend" action — reuses the same
 * cooldown/attempt-reset logic either way. */
export async function requestPasswordResetOtp(email: string): Promise<void> {
  const user = await usersRepo.findOne((u) => u.email.toLowerCase() === email.toLowerCase());
  if (!user || user.status !== "ACTIVE") return;

  const existing = await passwordResetOtpsRepo.findMany((r) => r.userId === user.id && !r.used);
  const latest = existing.sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0];
  if (latest && Date.now() - new Date(latest.lastSentAt).getTime() < RESEND_COOLDOWN_MS) {
    const waitSec = Math.ceil((RESEND_COOLDOWN_MS - (Date.now() - new Date(latest.lastSentAt).getTime())) / 1000);
    throw new AppError("ERR_VALIDATION", `Please wait ${waitSec}s before requesting another code.`);
  }

  // Invalidate any still-outstanding codes so only the newest one can ever succeed.
  await Promise.all(existing.map((r) => passwordResetOtpsRepo.update(r.id, { used: true })));

  const otp = generateOtp();
  const id = await nextId("OTP");
  const now = new Date().toISOString();
  const record: PasswordResetOtp = {
    id,
    userId: user.id,
    email: user.email,
    otpHash: hashOtp(otp),
    expiresAt: new Date(Date.now() + OTP_TTL_MS).toISOString(),
    used: false,
    verified: false,
    attempts: 0,
    maxAttempts: MAX_ATTEMPTS,
    lastSentAt: now,
    createdAt: now,
    updatedAt: now,
  };
  await passwordResetOtpsRepo.insert(record);

  await sendEmail(
    user.email,
    "PASSWORD_RESET_OTP",
    "Your Factory Fleet Management password reset code",
    `Hi ${user.fullName},\n\nYour one-time password reset code is: ${otp}\n\nThis code expires in 5 minutes. If you didn't request this, you can safely ignore this email.`
  );

  await writeAudit(user.id, "User", "UPDATE", user.id, "Password reset OTP requested");
}

/** Alias kept for readability at call sites — identical throttling/invalidation logic. */
export const resendPasswordResetOtp = requestPasswordResetOtp;

async function findActiveOtpRecord(email: string): Promise<PasswordResetOtp | undefined> {
  const records = await passwordResetOtpsRepo.findMany((r) => r.email.toLowerCase() === email.toLowerCase() && !r.used);
  return records.sort((a, b) => b.createdAt.localeCompare(a.createdAt))[0];
}

export interface VerifyOtpResult {
  resetTicket: string;
}

/** Requirements #6-9 & #15: verify the code, track wrong attempts, expire it,
 * and lock it out after too many failures (forcing the user to resend). */
export async function verifyPasswordResetOtp(email: string, otp: string): Promise<VerifyOtpResult> {
  const record = await findActiveOtpRecord(email);
  if (!record) {
    throw new AppError("ERR_VALIDATION", "Invalid or expired code. Please request a new one.");
  }

  if (new Date(record.expiresAt) < new Date()) {
    await passwordResetOtpsRepo.update(record.id, { used: true });
    throw new AppError("ERR_VALIDATION", "This code has expired. Please request a new one.");
  }

  if (record.attempts >= record.maxAttempts) {
    await passwordResetOtpsRepo.update(record.id, { used: true });
    throw new AppError("ERR_VALIDATION", "Too many incorrect attempts. Please request a new code.");
  }

  if (record.otpHash !== hashOtp(otp)) {
    const attempts = record.attempts + 1;
    const lockedOut = attempts >= record.maxAttempts;
    await passwordResetOtpsRepo.update(record.id, { attempts, used: lockedOut });
    if (lockedOut) {
      throw new AppError("ERR_VALIDATION", "Too many incorrect attempts. Please request a new code.");
    }
    const remaining = record.maxAttempts - attempts;
    throw new AppError("ERR_VALIDATION", `Incorrect code. ${remaining} attempt${remaining === 1 ? "" : "s"} left.`);
  }

  await passwordResetOtpsRepo.update(record.id, { verified: true, attempts: 0 });

  const resetTicket = issueResetTicket({ otpId: record.id, userId: record.userId, exp: Date.now() + TICKET_TTL_MS });
  return { resetTicket };
}

/** Requirements #11-14: the final step — spend the one-time verified ticket to set a new password. */
export async function resetPasswordWithOtp(resetTicket: string, newPassword: string): Promise<void> {
  const payload = readResetTicket(resetTicket);

  const record = await passwordResetOtpsRepo.findById(payload.otpId);
  if (!record || record.userId !== payload.userId || !record.verified || record.used) {
    throw new AppError("ERR_VALIDATION", "This session has expired. Please verify your code again.");
  }

  const user = await usersRepo.findById(record.userId);
  if (!user) throw new AppError("ERR_NOT_FOUND", "Account not found.");

  const passwordHash = await hashPassword(newPassword);
  await usersRepo.update(user.id, { passwordHash });
  await passwordResetOtpsRepo.update(record.id, { used: true });

  await writeAudit(user.id, "User", "UPDATE", user.id, "Password reset completed via OTP");
  await createNotification(user.id, "Password Changed", "Your password was just reset. If this wasn't you, contact an administrator immediately.", "SYSTEM");
  await sendEmail(
    user.email,
    "PASSWORD_RESET_COMPLETED",
    "Your password has been changed",
    `Hi ${user.fullName}, your Factory Fleet Management password was just changed. If this wasn't you, contact an administrator immediately.`
  );
}
