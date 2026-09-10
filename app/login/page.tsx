import Link from "next/link";
import { CheckCircle2, Car, ShieldCheck, Clock3 } from "lucide-react";
import { LoginForm } from "./login-form";
import { departmentsRepo } from "@/lib/json-db/repositories";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ registered?: string; reset?: string }>;
}) {
  const params = await searchParams;
  const departments = (await departmentsRepo.findAll()).filter((d) => d.status === "ACTIVE");

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Hero panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-[#0f1222] p-12 text-white lg:flex">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.25),transparent_45%),radial-gradient(circle_at_80%_70%,rgba(139,92,246,0.2),transparent_45%)]" />
        <div className="relative flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-lg font-bold shadow-lg shadow-indigo-900/40">
            F
          </div>
          <span className="text-lg font-semibold">Factory Fleet Management</span>
        </div>

        <div className="relative space-y-6">
          <h1 className="text-3xl font-semibold leading-tight text-white">
            Every vehicle,
            <br />
            every trip, one dashboard.
          </h1>
          <p className="max-w-sm text-sm text-slate-400">
            Book, approve, track, and report on your fleet — with a full audit trail and
            real-time availability, from request to trip completion.
          </p>
          <div className="space-y-3 pt-2">
            <Feature icon={Car} text="Live vehicle & driver availability" />
            <Feature icon={ShieldCheck} text="Role-based approvals with a full audit log" />
            <Feature icon={Clock3} text="Trip start to finish, tracked automatically" />
          </div>
        </div>

        <p className="relative text-xs text-slate-600">© {new Date().getFullYear()} Factory Fleet Management</p>
      </div>

      {/* Form panel */}
      <div className="flex w-full items-center justify-center px-4 py-10 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center lg:text-left">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-xl font-bold text-white shadow-lg shadow-indigo-600/20 lg:hidden">
              F
            </div>
            <h1 className="text-2xl font-semibold text-slate-900">Welcome back</h1>
            <p className="mt-1 text-sm text-slate-500">Sign in to your fleet dashboard</p>
          </div>

          {params.registered && (
            <div className="mb-4 flex items-start gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700 ring-1 ring-inset ring-emerald-200">
              <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
              Registration submitted! Your account is pending admin approval.
            </div>
          )}
          {params.reset && (
            <div className="mb-4 flex items-start gap-2 rounded-xl bg-emerald-50 px-4 py-3 text-sm text-emerald-700 ring-1 ring-inset ring-emerald-200">
              <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
              Your password has been reset. Please sign in with your new password.
            </div>
          )}

          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
            <LoginForm departments={departments} />
          </div>

          <p className="mt-6 text-center text-sm text-slate-500">
            Don&apos;t have an account?{" "}
            <Link href="/signup" className="font-medium text-indigo-600 hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

function Feature({ icon: Icon, text }: { icon: typeof Car; text: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-slate-300">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10">
        <Icon size={16} />
      </div>
      {text}
    </div>
  );
}
