"use client";

import {
  useActionState,
  useEffect,
  useRef,
  useState,
  type ChangeEvent,
  type RefObject,
} from "react";
import {
  User,
  Mail,
  Phone,
  Hash,
  Building2,
  Briefcase,
  Lock,
  MapPin,
  Check,
  Loader2,
} from "lucide-react";
import { signupAction, type ActionState } from "@/lib/actions/auth-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { Department } from "@/lib/types";

const initialState: ActionState = {};

const STEPS = [
  { n: 1, label: "Personal" },
  { n: 2, label: "Work" },
  { n: 3, label: "Security" },
] as const;

// Which step each field belongs to, so a server-side validation error can
// jump the wizard back to the right step automatically.
const FIELD_STEP: Record<string, number> = {
  fullName: 1,
  email: 1,
  phone: 1,
  employeeId: 2,
  departmentId: 2,
  designation: 2,
  password: 3,
  confirmPassword: 3,
  address: 3,
};

export function SignupForm({ departments }: { departments: Department[] }) {
  const [state, formAction, pending] = useActionState(signupAction, initialState);
  const errors = state.fieldErrors || {};

  const [step, setStep] = useState(1);
  const step1Ref = useRef<HTMLDivElement>(null);
  const step2Ref = useRef<HTMLDivElement>(null);

  const [password, setPassword] = useState("");
  const confirmRef = useRef<HTMLInputElement>(null);

  // If the server returns field errors, jump back to the earliest step that needs fixing.
  useEffect(() => {
    const keys = Object.keys(errors);
    if (keys.length === 0) return;
    const targetStep = Math.min(...keys.map((k) => FIELD_STEP[k] ?? 3));
    setStep(targetStep);
  }, [state]); // eslint-disable-line react-hooks/exhaustive-deps

  function goNext(ref: RefObject<HTMLDivElement | null>, next: number) {
    const container = ref.current;
    if (container) {
      const controls = container.querySelectorAll<HTMLInputElement | HTMLSelectElement>(
        "input, select"
      );
      for (const el of Array.from(controls)) {
        if (!el.checkValidity()) {
          el.reportValidity();
          return;
        }
      }
    }
    setStep(next);
  }

  function handlePasswordChange(e: ChangeEvent<HTMLInputElement>) {
    const value = e.target.value;
    setPassword(value);
    if (confirmRef.current && confirmRef.current.value) {
      confirmRef.current.setCustomValidity(
        confirmRef.current.value !== value ? "Passwords do not match" : ""
      );
    }
  }

  function handleConfirmChange(e: ChangeEvent<HTMLInputElement>) {
    e.target.setCustomValidity(e.target.value !== password ? "Passwords do not match" : "");
  }

  return (
    <form action={formAction} className="space-y-6">
      {state.error && (
        <div className="rounded-xl border border-rose-100 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700">
          {state.error}
        </div>
      )}

      {/* Progress indicator */}
      <div className="flex items-center">
        {STEPS.map((s, i) => (
          <div key={s.n} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold transition ${
                  step > s.n
                    ? "bg-indigo-600 text-white"
                    : step === s.n
                      ? "bg-indigo-600 text-white ring-4 ring-indigo-100"
                      : "bg-slate-100 text-slate-400"
                }`}
              >
                {step > s.n ? <Check className="h-4 w-4" /> : s.n}
              </div>
              <span
                className={`text-[11px] font-medium ${
                  step >= s.n ? "text-indigo-600" : "text-slate-400"
                }`}
              >
                {s.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`mx-2 mb-4 h-0.5 flex-1 rounded-full transition ${
                  step > s.n ? "bg-indigo-600" : "bg-slate-100"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Step 1 — Personal details */}
      <div ref={step1Ref} className={step === 1 ? "space-y-4" : "hidden"}>
        <Field label="Full Name" required error={errors.fullName}>
          <div className="relative">
            <input name="fullName" required className={`peer ${inputClass} pl-10`} />
            <User className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
          </div>
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Email" required error={errors.email}>
            <div className="relative">
              <input
                name="email"
                type="email"
                required
                className={`peer ${inputClass} pl-10`}
              />
              <Mail className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
            </div>
          </Field>
          <Field label="Phone" required error={errors.phone}>
            <div className="relative">
              <input name="phone" required className={`peer ${inputClass} pl-10`} />
              <Phone className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
            </div>
          </Field>
        </div>

        <Button
          type="button"
          onClick={() => goNext(step1Ref, 2)}
          className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 py-2.5 font-medium shadow-lg shadow-indigo-500/25 transition hover:shadow-xl hover:shadow-indigo-500/40"
        >
          Continue
        </Button>
      </div>

      {/* Step 2 — Work details */}
      <div ref={step2Ref} className={step === 2 ? "space-y-4" : "hidden"}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Employee ID">
            <div className="relative">
              <input name="employeeId" className={`peer ${inputClass} pl-10`} />
              <Hash className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
            </div>
          </Field>
          <Field label="Department" required error={errors.departmentId}>
            <div className="relative">
              <select
                name="departmentId"
                required
                defaultValue=""
                className={`peer ${inputClass} pl-10`}
              >
                <option value="" disabled>
                  Select department
                </option>
                {departments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
              <Building2 className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
            </div>
          </Field>
        </div>

        <Field label="Designation" required error={errors.designation}>
          <div className="relative">
            <input name="designation" required className={`peer ${inputClass} pl-10`} />
            <Briefcase className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
          </div>
        </Field>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setStep(1)}
            className="w-full rounded-xl border border-slate-200 bg-white py-2.5 font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
          >
            Back
          </Button>
          <Button
            type="button"
            onClick={() => goNext(step2Ref, 3)}
            className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 py-2.5 font-medium shadow-lg shadow-indigo-500/25 transition hover:shadow-xl hover:shadow-indigo-500/40"
          >
            Continue
          </Button>
        </div>
      </div>

      {/* Step 3 — Security */}
      <div className={step === 3 ? "space-y-4" : "hidden"}>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Password" required error={errors.password}>
            <div className="relative">
              <input
                name="password"
                type="password"
                required
                minLength={8}
                onChange={handlePasswordChange}
                className={`peer ${inputClass} pl-10`}
              />
              <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
            </div>
          </Field>
          <Field label="Confirm Password" required error={errors.confirmPassword}>
            <div className="relative">
              <input
                ref={confirmRef}
                name="confirmPassword"
                type="password"
                required
                onChange={handleConfirmChange}
                className={`peer ${inputClass} pl-10`}
              />
              <Lock className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
            </div>
          </Field>
        </div>

        <Field label="Address (optional)">
          <div className="relative">
            <input name="address" className={`peer ${inputClass} pl-10`} />
            <MapPin className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 transition-colors peer-focus:text-indigo-500" />
          </div>
        </Field>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => setStep(2)}
            className="w-full rounded-xl border border-slate-200 bg-white py-2.5 font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
          >
            Back
          </Button>
          <Button
            type="submit"
            disabled={pending}
            className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 py-2.5 font-medium shadow-lg shadow-indigo-500/25 transition hover:shadow-xl hover:shadow-indigo-500/40"
          >
            {pending ? (
              <span className="flex items-center justify-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </span>
            ) : (
              "Create account"
            )}
          </Button>
        </div>
      </div>
    </form>
  );
}