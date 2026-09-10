"use server";

import { redirect } from "next/navigation";
import { signupSchema, loginSchema, requestResetSchema, verifyOtpSchema, resetPasswordWithOtpSchema } from "@/lib/validators/auth";
import { registerEmployee, authenticate } from "@/lib/services/auth-service";
import { requestPasswordResetOtp, resendPasswordResetOtp, verifyPasswordResetOtp, resetPasswordWithOtp } from "@/lib/services/password-reset-service";
import { createSession, destroySession } from "@/lib/auth/session";

export interface ActionState {
  error?: string;
  fieldErrors?: Record<string, string>;
  success?: boolean;
  resetTicket?: string;
}

export async function signupAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const raw = Object.fromEntries(formData.entries());
  const parsed = signupSchema.safeParse(raw);
  if (!parsed.success) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of parsed.error.issues) {
      fieldErrors[String(issue.path[0])] = issue.message;
    }
    return { error: "Please fix the errors below.", fieldErrors };
  }

  try {
    await registerEmployee(parsed.data);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "Registration failed." };
  }

  redirect("/login?registered=1");
}

export async function loginAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const raw = Object.fromEntries(formData.entries());
  const parsed = loginSchema.safeParse({
    email: raw.email,
    password: raw.password,
    remember: raw.remember === "on",
  });
  if (!parsed.success) {
    return { error: "Enter a valid email and password." };
  }

  let user;
  try {
    user = await authenticate(parsed.data.email, parsed.data.password);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "Login failed." };
  }

  if (user.status === "PENDING") {
    return { error: "Your account is pending admin approval." };
  }
  if (user.status === "REJECTED") {
    return { error: `Your registration was rejected.${user.rejectionReason ? " Reason: " + user.rejectionReason : ""}` };
  }
  if (user.status === "SUSPENDED") {
    return { error: "Your account has been suspended. Contact an administrator." };
  }

  await createSession(
    { userId: user.id, role: user.role, fullName: user.fullName, email: user.email },
    parsed.data.remember ?? false
  );

  redirect("/dashboard");
}

export async function logoutAction() {
  await destroySession();
  redirect("/login");
}

export async function requestOtpAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const raw = Object.fromEntries(formData.entries());
  const parsed = requestResetSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message || "Enter a valid email address." };
  }

  try {
    await requestPasswordResetOtp(parsed.data.email);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "Could not send the code." };
  }
  // Always report success (whether or not the email exists) to avoid account enumeration.
  return { success: true };
}

export async function resendOtpAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const raw = Object.fromEntries(formData.entries());
  const parsed = requestResetSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message || "Enter a valid email address." };
  }

  try {
    await resendPasswordResetOtp(parsed.data.email);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "Could not resend the code." };
  }
  return { success: true };
}

export async function verifyOtpAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const raw = Object.fromEntries(formData.entries());
  const parsed = verifyOtpSchema.safeParse(raw);
  if (!parsed.success) {
    return { error: parsed.error.issues[0]?.message || "Enter the 6-digit code." };
  }

  try {
    const { resetTicket } = await verifyPasswordResetOtp(parsed.data.email, parsed.data.otp);
    return { success: true, resetTicket };
  } catch (err) {
    return { error: err instanceof Error ? err.message : "Could not verify the code." };
  }
}

export async function resetPasswordWithOtpAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const raw = Object.fromEntries(formData.entries());
  const parsed = resetPasswordWithOtpSchema.safeParse(raw);
  if (!parsed.success) {
    const fieldErrors: Record<string, string> = {};
    for (const issue of parsed.error.issues) fieldErrors[String(issue.path[0])] = issue.message;
    return { error: "Please fix the errors below.", fieldErrors };
  }

  try {
    await resetPasswordWithOtp(parsed.data.resetTicket, parsed.data.password);
  } catch (err) {
    return { error: err instanceof Error ? err.message : "Could not reset your password." };
  }

  redirect("/login?reset=1");
}
