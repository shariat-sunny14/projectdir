import Link from "next/link";
import { ShieldCheck, Wrench, Users } from "lucide-react";
import { departmentsRepo } from "@/lib/json-db/repositories";
import { SignupShell } from "./signup-shell";
import { SignupForm } from "./signup-form";

export default async function SignupPage() {
  const departments = (await departmentsRepo.findAll()).filter((d) => d.status === "ACTIVE");

  return (
    <SignupShell
      title={
        <>
          Join your team on
          <br /> Factory Fleet.
        </>
      }
      subtitle="Create your account in a few quick steps. New accounts start as Employee and are activated once your admin approves them."
      features={[
        { icon: Users, text: "See only the vehicles & jobs assigned to you" },
        { icon: Wrench, text: "Log trips, requests, and maintenance in seconds" },
        { icon: ShieldCheck, text: "Every account is reviewed before activation" },
      ]}
      stats={[
        { value: "1,200+", label: "Vehicles tracked" },
        { value: "300+", label: "Active drivers" },
        { value: "< 24h", label: "Avg. approval time" },
      ]}
      maxWidth="lg"
    >
      <div className="rounded-2xl border border-slate-100 bg-white p-8 shadow-xl shadow-slate-200/60 sm:p-10">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-xl font-bold text-white shadow-lg shadow-indigo-500/30">
            F
          </div>
          <h1 className="text-xl font-semibold text-slate-900">Create your account</h1>
          <p className="mt-1 text-sm text-slate-500">
            New accounts start as <span className="font-medium">Employee</span> and require
            admin approval.
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
    </SignupShell>
  );
}