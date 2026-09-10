import type { LucideIcon } from "lucide-react";

export function StatCard({
  label,
  value,
  icon: Icon,
  tone = "indigo",
}: {
  label: string;
  value: string | number;
  icon: LucideIcon;
  tone?: "indigo" | "emerald" | "amber" | "rose" | "blue";
}) {
  const toneClasses: Record<string, string> = {
    indigo: "bg-gradient-to-br from-indigo-500 to-violet-600 shadow-indigo-500/30",
    emerald: "bg-gradient-to-br from-emerald-500 to-teal-600 shadow-emerald-500/30",
    amber: "bg-gradient-to-br from-amber-400 to-orange-500 shadow-amber-500/30",
    rose: "bg-gradient-to-br from-rose-500 to-pink-600 shadow-rose-500/30",
    blue: "bg-gradient-to-br from-blue-500 to-cyan-600 shadow-blue-500/30",
  };

  return (
    <div className="group rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50 transition-shadow hover:shadow-md">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <div className={`flex h-9 w-9 items-center justify-center rounded-xl text-white shadow-lg ${toneClasses[tone]}`}>
          <Icon size={16} />
        </div>
      </div>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-900">{value}</p>
    </div>
  );
}
