"use client";

import { useRef } from "react";
import { Clock } from "lucide-react";

export function TimePicker({
  value,
  onChange,
  required,
  className = "",
}: {
  value: string;
  onChange: (v: string) => void;
  required?: boolean;
  className?: string;
}) {
  const ref = useRef<HTMLInputElement>(null);

  function openPicker() {
    const el = ref.current;
    if (!el) return;
    // showPicker() opens the native time UI on click, not just on focus caret.
    if ("showPicker" in el && typeof el.showPicker === "function") {
      try {
        el.showPicker();
      } catch {
        el.focus();
      }
    } else {
      el.focus();
    }
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <input
        ref={ref}
        type="time"
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onClick={openPicker}
        className="w-full bg-transparent text-sm text-slate-900 outline-none [&::-webkit-calendar-picker-indicator]:hidden"
      />
      <button type="button" onClick={openPicker} className="text-slate-400 hover:text-indigo-600" tabIndex={-1}>
        <Clock size={16} />
      </button>
    </div>
  );
}
