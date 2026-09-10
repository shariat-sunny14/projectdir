"use client";

import { useActionState } from "react";
import { signupAction, type ActionState } from "@/lib/actions/auth-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { GoogleSignInButton } from "@/components/auth/google-signin-button";
import type { Department } from "@/lib/types";

const initialState: ActionState = {};

export function SignupForm({ departments }: { departments: Department[] }) {
  const [state, formAction, pending] = useActionState(signupAction, initialState);
  const errors = state.fieldErrors || {};

  return (
    <div className="space-y-4">
      <form action={formAction} className="space-y-4">
        {state.error && (
          <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{state.error}</div>
        )}

        <Field label="Full Name" required error={errors.fullName}>
          <input name="fullName" required className={inputClass} />
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Email" required error={errors.email}>
            <input name="email" type="email" required className={inputClass} />
          </Field>
          <Field label="Phone" required error={errors.phone}>
            <input name="phone" required className={inputClass} />
          </Field>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Employee ID">
            <input name="employeeId" className={inputClass} />
          </Field>
          <Field label="Department" required error={errors.departmentId}>
            <select name="departmentId" required className={inputClass} defaultValue="">
              <option value="" disabled>
                Select department
              </option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </Field>
        </div>

        <Field label="Designation" required error={errors.designation}>
          <input name="designation" required className={inputClass} />
        </Field>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Field label="Password" required error={errors.password}>
            <input name="password" type="password" required className={inputClass} />
          </Field>
          <Field label="Confirm Password" required error={errors.confirmPassword}>
            <input name="confirmPassword" type="password" required className={inputClass} />
          </Field>
        </div>

        <Field label="Address (optional)">
          <input name="address" className={inputClass} />
        </Field>

        <Button type="submit" disabled={pending} className="w-full">
          {pending ? "Submitting..." : "Create account"}
        </Button>
      </form>

      <div className="relative py-2 text-center text-xs text-slate-400">
        <span className="bg-white px-2">OR</span>
        <div className="absolute left-0 top-1/2 -z-10 h-px w-full bg-slate-200" />
      </div>

      <GoogleSignInButton departments={departments} />
    </div>
  );
}
