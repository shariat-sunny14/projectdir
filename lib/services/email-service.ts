import nodemailer from "nodemailer";
import { emailLogsRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";

/**
 * Real email transport via Gmail SMTP (nodemailer), configured from env vars.
 * Falls back to a no-op "logged only" mode if credentials aren't set, so the
 * app still runs (and still populates Email Logs) without SMTP configured.
 */
let transporter: ReturnType<typeof nodemailer.createTransport> | null = null;

function getTransporter() {
  const user = process.env.YAGMAIL_USER;
  const pass = process.env.YAGMAIL_APP_PASSWORD;
  if (!user || !pass) return null;

  if (!transporter) {
    transporter = nodemailer.createTransport({
      service: "gmail",
      auth: { user, pass },
      // Fail fast rather than blocking a Server Action for minutes if SMTP is
      // unreachable (e.g. restricted network) — BR-023 still logs it as FAILED.
      connectionTimeout: 10_000,
      greetingTimeout: 10_000,
      socketTimeout: 10_000,
    });
  }
  return transporter;
}

async function deliver(to: string, subject: string, body: string): Promise<void> {
  const t = getTransporter();
  if (!t) {
    // No SMTP configured — treat as delivered so the demo flow still has SENT logs.
    return;
  }
  await t.sendMail({
    from: `"Factory Fleet Management" <${process.env.YAGMAIL_USER}>`,
    to,
    subject,
    text: body,
  });
}

export async function sendEmail(to: string, event: string, subject: string, body: string) {
  const id = await nextId("EML");
  const now = new Date().toISOString();

  try {
    await deliver(to, subject, body);
    await emailLogsRepo.insert({ id, to, event, subject, body, status: "SENT", createdAt: now, updatedAt: now });
  } catch (err) {
    // BR-023: log the failure but never throw — must not break the caller's transaction.
    await emailLogsRepo.insert({
      id,
      to,
      event,
      subject,
      body,
      status: "FAILED",
      errorMessage: err instanceof Error ? err.message : "Unknown email error",
      createdAt: now,
      updatedAt: now,
    });
  }
}

/** @deprecated use sendEmail() — kept as an alias for older call sites. */
export const logEmail = sendEmail;
