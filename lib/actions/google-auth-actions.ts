"use server";

import crypto from "crypto";
import { redirect } from "next/navigation";
import { usersRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { verifyGoogleIdToken } from "@/lib/services/google-auth-service";
import { hashPassword } from "@/lib/auth/password";
import { createSession } from "@/lib/auth/session";
import { sendEmail } from "@/lib/services/email-service";
import { writeAudit } from "@/lib/services/audit-service";
import { runAction, type ActionResult } from "@/lib/errors";

export interface GoogleSignInResult {
  status: "signed_in" | "needs_profile" | "pending" | "rejected" | "suspended";
  email?: string;
  name?: string;
  picture?: string;
  message?: string;
}

/** Called right after the Google Identity Services button returns an ID token.
 * Verifies it server-side, then either logs the existing user in or reports that
 * a first-time Google sign-up needs a few more profile fields before we can create
 * the (still PENDING, admin-approved) account. */
export async function googleSignInAction(idToken: string): Promise<ActionResult<GoogleSignInResult>> {
  return runAction(async () => {
    const profile = await verifyGoogleIdToken(idToken);

    const existing = await usersRepo.findOne((u) => u.email.toLowerCase() === profile.email.toLowerCase());

    if (!existing) {
      return { status: "needs_profile", email: profile.email, name: profile.name, picture: profile.picture };
    }

    if (existing.status === "PENDING") {
      return { status: "pending", message: "Your account is pending admin approval." };
    }
    if (existing.status === "REJECTED") {
      return { status: "rejected", message: `Your registration was rejected.${existing.rejectionReason ? " Reason: " + existing.rejectionReason : ""}` };
    }
    if (existing.status === "SUSPENDED") {
      return { status: "suspended", message: "Your account has been suspended. Contact an administrator." };
    }

    // Link the Google account on first successful Google login for an existing
    // email/password user, so future sign-ins can use either method.
    if (!existing.googleId) {
      await usersRepo.update(existing.id, { googleId: profile.googleId });
    }

    await createSession({ userId: existing.id, role: existing.role, fullName: existing.fullName, email: existing.email }, false);
    await writeAudit(existing.id, "User", "LOGIN", existing.id, "Signed in with Google");

    return { status: "signed_in" };
  });
}

/** Completes a first-time Google sign-up: collects the fields Google doesn't give us
 * (phone, department, designation), creates a PENDING EMPLOYEE account exactly like the
 * normal sign-up flow, and requires the same admin approval. */
export async function completeGoogleSignupAction(formData: FormData) {
  const idToken = String(formData.get("idToken") || "");
  const profile = await verifyGoogleIdToken(idToken);

  const existing = await usersRepo.findOne((u) => u.email.toLowerCase() === profile.email.toLowerCase());
  if (existing) {
    redirect("/login");
  }

  const phone = String(formData.get("phone") || "");
  const departmentId = String(formData.get("departmentId") || "");
  const designation = String(formData.get("designation") || "");
  if (!phone || !departmentId || !designation) {
    throw new Error("Phone, department, and designation are required.");
  }

  const id = await nextId("USR");
  // Google-authenticated accounts don't set their own password; generate an unusable
  // random one. They can still use "Forgot password" later to set a real one if needed.
  const passwordHash = await hashPassword(crypto.randomBytes(32).toString("hex"));
  const now = new Date().toISOString();

  await usersRepo.insert({
    id,
    fullName: profile.name,
    email: profile.email,
    phone,
    departmentId,
    designation,
    passwordHash,
    googleId: profile.googleId,
    role: "EMPLOYEE",
    status: "PENDING",
    profileImage: profile.picture,
    createdAt: now,
    updatedAt: now,
  });

  await sendEmail(profile.email, "REGISTRATION_SUBMITTED", "Registration received", `Hi ${profile.name}, your registration (via Google) is pending admin approval.`);
  await writeAudit(id, "User", "CREATE", id, "Self-registration via Google");

  redirect("/login?registered=1");
}
