import type { LucideIcon } from "lucide-react";

type Feature = { icon: LucideIcon; text: string };
type Stat = { value: string; label: string };

export function SignupShell({
  eyebrow = "Factory Fleet Management",
  title,
  subtitle,
  features,
  stats,
  maxWidth = "md",
  children,
}: {
  eyebrow?: string;
  title: React.ReactNode;
  subtitle: string;
  features: Feature[];
  stats?: Stat[];
  maxWidth?: "md" | "lg";
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen w-full bg-slate-50">
      {/* Left — hero / brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-[#0f1222] p-12 text-white lg:flex xl:p-16">
        {/* Subtle glow */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.25),transparent_45%),radial-gradient(circle_at_80%_70%,rgba(139,92,246,0.2),transparent_45%)]" />

        {/* Faint grid overlay */}
        <div
          className="absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "linear-gradient(to right, white 1px, transparent 1px), linear-gradient(to bottom, white 1px, transparent 1px)",
            backgroundSize: "42px 42px",
          }}
        />

        {/* Logo */}
        <div className="relative flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-lg font-bold shadow-lg shadow-indigo-900/40">
            F
          </div>
          <span className="text-lg font-semibold tracking-tight">{eyebrow}</span>
        </div>

        {/* Headline + features */}
        <div className="relative max-w-sm space-y-6">
          <h1 className="text-3xl font-semibold leading-tight text-white xl:text-4xl">
            {title}
          </h1>
          <p className="text-sm leading-relaxed text-slate-400">{subtitle}</p>

          {features && features.length > 0 && (
            <div className="space-y-3 pt-2">
              {features.map((f, i) => (
                <div key={i} className="flex items-center gap-3 text-sm text-slate-300">
                  <span className="flex h-8 w-8 flex-none items-center justify-center rounded-lg bg-white/5 ring-1 ring-inset ring-white/10">
                    <f.icon size={16} className="text-indigo-300" />
                  </span>
                  {f.text}
                </div>
              ))}
            </div>
          )}

          {stats && stats.length > 0 && (
            <div className="grid grid-cols-3 gap-4 border-t border-white/10 pt-6">
              {stats.map((s, i) => (
                <div key={i}>
                  <p className="text-2xl font-semibold text-white">{s.value}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{s.label}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="relative text-xs text-slate-600">
          © {new Date().getFullYear()} {eyebrow}. All rights reserved.
        </p>
      </div>

      {/* Right — form panel */}
      <div className="flex w-full items-center justify-center px-4 py-10 lg:w-1/2">
        <div className={`w-full ${maxWidth === "lg" ? "max-w-lg" : "max-w-md"}`}>
          {/* Mobile-only logo */}
          <div className="mx-auto mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-xl font-bold text-white shadow-lg shadow-indigo-600/20 lg:hidden">
            F
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm shadow-slate-200/60">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}