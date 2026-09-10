"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Calendar, X } from "lucide-react";
import { DatePicker } from "@/components/ui/date-picker";

function toIso(d: Date) {
  return d.toISOString().slice(0, 10);
}

function preset(days: number | "month" | "6month" | "year") {
  const to = new Date();
  const from = new Date();
  if (days === "month") from.setMonth(from.getMonth() - 1);
  else if (days === "6month") from.setMonth(from.getMonth() - 6);
  else if (days === "year") from.setFullYear(from.getFullYear() - 1);
  else from.setDate(from.getDate() - (days - 1));
  return { from: toIso(from), to: toIso(to) };
}

const PRESETS: { label: string; get: () => { from: string; to: string } }[] = [
  { label: "Today", get: () => preset(1) },
  { label: "Last 7 Days", get: () => preset(7) },
  { label: "Last Month", get: () => preset("month") },
  { label: "Last 6 Months", get: () => preset("6month") },
  { label: "Last 1 Year", get: () => preset("year") },
];

export function DateRangeFilter({ dateLabel = "Date" }: { dateLabel?: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentFrom = searchParams.get("from") || "";
  const currentTo = searchParams.get("to") || "";
  const [customOpen, setCustomOpen] = useState(false);
  const [from, setFrom] = useState(currentFrom);
  const [to, setTo] = useState(currentTo);

  function apply(newFrom: string, newTo: string) {
    const params = new URLSearchParams(searchParams.toString());
    if (newFrom) params.set("from", newFrom);
    else params.delete("from");
    if (newTo) params.set("to", newTo);
    else params.delete("to");
    params.delete("page"); // reset pagination whenever the filter changes
    router.push(`${pathname}?${params.toString()}`);
  }

  function clear() {
    setFrom("");
    setTo("");
    apply("", "");
    setCustomOpen(false);
  }

  const activeLabel =
    currentFrom || currentTo ? `${currentFrom || "…"} → ${currentTo || "…"}` : null;

  return (
    <div className="flex flex-wrap items-center gap-2">
      {PRESETS.map((p) => (
        <button
          key={p.label}
          onClick={() => {
            const r = p.get();
            setFrom(r.from);
            setTo(r.to);
            apply(r.from, r.to);
          }}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm hover:border-indigo-300 hover:text-indigo-600"
        >
          {p.label}
        </button>
      ))}

      <div className="relative">
        <button
          onClick={() => setCustomOpen((v) => !v)}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 shadow-sm hover:border-indigo-300 hover:text-indigo-600"
        >
          <Calendar size={12} />
          {activeLabel || `${dateLabel} range`}
        </button>

        {customOpen && (
          <div className="absolute right-0 z-40 mt-2 w-64 rounded-xl border border-slate-200 bg-white p-3 shadow-xl">
            <p className="mb-2 text-xs font-semibold text-slate-500">From — To</p>
            <div className="space-y-2">
              <DatePicker value={from} onChange={setFrom} className="rounded-lg border border-slate-200 px-2 py-1.5" />
              <DatePicker value={to} onChange={setTo} className="rounded-lg border border-slate-200 px-2 py-1.5" />
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <button onClick={() => setCustomOpen(false)} className="text-xs font-medium text-slate-500 hover:text-slate-700">
                Cancel
              </button>
              <button
                onClick={() => {
                  apply(from, to);
                  setCustomOpen(false);
                }}
                className="rounded-lg bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-700"
              >
                Apply
              </button>
            </div>
          </div>
        )}
      </div>

      {activeLabel && (
        <button onClick={clear} className="inline-flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-rose-600">
          <X size={12} /> Clear
        </button>
      )}
    </div>
  );
}
