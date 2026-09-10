"use client";

import Link from "next/link";
import { useActionState } from "react";
import { loginAction, type ActionState } from "@/lib/actions/auth-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { GoogleSignInButton } from "@/components/auth/google-signin-button";
import type { Department } from "@/lib/types";

const initialState: ActionState = {};

export function LoginForm({ departments }: { departments: Department[] }) {
  const [state, formAction, pending] = useActionState(loginAction, initialState);

  return (
    <div className="space-y-4">
      <form action={formAction} className="space-y-4">
        {state.error && (
          <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{state.error}</div>
        )}

        <Field label="Email" required>
          <input name="email" type="email" required className={inputClass} placeholder="you@company.com" />
        </Field>

        <Field label="Password" required>
          <input name="password" type="password" required className={inputClass} placeholder="••••••••" />
        </Field>

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-slate-600">
            <input type="checkbox" name="remember" className="rounded border-slate-300" />
            Remember me
          </label>
          <Link href="/forgot-password" className="font-medium text-indigo-600 hover:underline">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" disabled={pending} className="w-full">
          {pending ? "Signing in..." : "Sign in"}
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
