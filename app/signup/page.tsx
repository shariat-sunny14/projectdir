import Link from "next/link";
import { departmentsRepo } from "@/lib/json-db/repositories";
import { SignupForm } from "./signup-form";

export default async function SignupPage() {
  const departments = (await departmentsRepo.findAll()).filter((d) => d.status === "ACTIVE");

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#0f1222] px-4 py-10">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_10%,rgba(99,102,241,0.25),transparent_45%),radial-gradient(circle_at_85%_90%,rgba(139,92,246,0.2),transparent_45%)]" />
      <div className="relative w-full max-w-lg rounded-2xl border border-white/10 bg-white p-8 shadow-2xl shadow-black/40">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-xl font-bold text-white shadow-lg shadow-indigo-600/30">
            F
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Create your account</h1>
          <p className="mt-1 text-sm text-slate-500">
            New accounts start as <span className="font-medium">Employee</span> and require admin approval.
          </p>
        </div>

        <SignupForm departments={departments} />

        <p className="mt-6 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-indigo-600 hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
