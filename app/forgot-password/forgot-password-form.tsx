"use client";

import { useActionState, useEffect, useState } from "react";
import { CheckCircle2, Mail, ShieldCheck, KeyRound, ArrowLeft } from "lucide-react";
import {
  requestOtpAction,
  resendOtpAction,
  verifyOtpAction,
  resetPasswordWithOtpAction,
  type ActionState,
} from "@/lib/actions/auth-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { OtpInput } from "@/components/ui/otp-input";

const initialState: ActionState = {};
const RESEND_COOLDOWN = 30;

type Step = "email" | "otp" | "password";

export function ForgotPasswordForm() {
  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [resetTicket, setResetTicket] = useState("");
  const [cooldown, setCooldown] = useState(0);

  const [requestState, requestAction, requestPending] = useActionState(requestOtpAction, initialState);
  const [resendState, resendAction, resendPending] = useActionState(resendOtpAction, initialState);
  const [verifyState, verifyAction, verifyPending] = useActionState(verifyOtpAction, initialState);
  const [resetState, resetAction, resetPending] = useActionState(resetPasswordWithOtpAction, initialState);

  // Step transitions are derived straight from each action's result during render
  // (React's recommended "adjusting state" pattern) rather than in an effect, since
  // each of these is a one-time reaction to a state object becoming a new reference.
  const [seenRequestState, setSeenRequestState] = useState(requestState);
  if (requestState !== seenRequestState) {
    setSeenRequestState(requestState);
    if (requestState.success && step === "email") {
      setStep("otp");
      setCooldown(RESEND_COOLDOWN);
    }
  }

  const [seenResendState, setSeenResendState] = useState(resendState);
  if (resendState !== seenResendState) {
    setSeenResendState(resendState);
    if (resendState.success) {
      setOtp("");
      setCooldown(RESEND_COOLDOWN);
    }
  }

  const [seenVerifyState, setSeenVerifyState] = useState(verifyState);
  if (verifyState !== seenVerifyState) {
    setSeenVerifyState(verifyState);
    if (verifyState.success && verifyState.resetTicket) {
      setResetTicket(verifyState.resetTicket);
      setStep("password");
    }
  }

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  if (step === "email") {
    return (
      <form action={requestAction} className="space-y-4">
        <StepBadge icon={<Mail size={16} />} text="Step 1 of 3 — Verify your email" />
        {requestState.error && <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{requestState.error}</div>}

        <Field label="Email" required>
          <input
            name="email"
            type="email"
            required
            className={inputClass}
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>

        <Button type="submit" disabled={requestPending} className="w-full">
          {requestPending ? "Sending code..." : "Send OTP Code"}
        </Button>
      </form>
    );
  }

  if (step === "otp") {
    return (
      <div className="space-y-4">
        <StepBadge icon={<ShieldCheck size={16} />} text="Step 2 of 3 — Enter the code" />
        <p className="text-center text-sm text-slate-500">
          We sent a 6-digit code to <strong className="text-slate-700">{email}</strong>. It expires in 5 minutes.
        </p>

        <form action={verifyAction} className="space-y-4">
          <input type="hidden" name="email" value={email} />
          <input type="hidden" name="otp" value={otp} />

          {verifyState.error && <div className="rounded-lg bg-rose-50 px-3 py-2 text-center text-sm text-rose-700">{verifyState.error}</div>}

          <OtpInput value={otp} onChange={setOtp} />

          <Button type="submit" disabled={verifyPending || otp.length !== 6} className="w-full">
            {verifyPending ? "Verifying..." : "Verify Code"}
          </Button>
        </form>

        <form action={resendAction} className="text-center">
          <input type="hidden" name="email" value={email} />
          {resendState.error && <p className="mb-1 text-xs text-rose-600">{resendState.error}</p>}
          {resendState.success && cooldown === RESEND_COOLDOWN && <p className="mb-1 text-xs text-emerald-600">A new code was sent.</p>}
          <button
            type="submit"
            disabled={resendPending || cooldown > 0}
            className="text-sm font-medium text-indigo-600 hover:underline disabled:text-slate-400 disabled:no-underline"
          >
            {cooldown > 0 ? `Resend code in ${cooldown}s` : resendPending ? "Resending..." : "Didn't get it? Resend code"}
          </button>
        </form>

        <button
          type="button"
          onClick={() => {
            setStep("email");
            setOtp("");
          }}
          className="mx-auto flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600"
        >
          <ArrowLeft size={12} /> Use a different email
        </button>
      </div>
    );
  }

  // step === "password"
  return (
    <form action={resetAction} className="space-y-4">
      <input type="hidden" name="resetTicket" value={resetTicket} />
      <StepBadge icon={<KeyRound size={16} />} text="Step 3 of 3 — Set a new password" />

      <div className="flex items-center justify-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
        <CheckCircle2 size={16} /> Code verified
      </div>

      {resetState.error && <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{resetState.error}</div>}

      <Field label="New Password" required error={resetState.fieldErrors?.password}>
        <input name="password" type="password" required className={inputClass} placeholder="••••••••" />
      </Field>
      <Field label="Confirm New Password" required error={resetState.fieldErrors?.confirmPassword}>
        <input name="confirmPassword" type="password" required className={inputClass} placeholder="••••••••" />
      </Field>

      <Button type="submit" disabled={resetPending} className="w-full">
        {resetPending ? "Saving..." : "Reset Password"}
      </Button>
    </form>
  );
}

function StepBadge({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="mx-auto flex w-fit items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-600">
      {icon}
      {text}
    </div>
  );
}
