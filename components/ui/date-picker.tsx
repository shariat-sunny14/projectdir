"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon } from "lucide-react";

function pad(n: number) {
  return String(n).padStart(2, "0");
}

function toIso(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function parseIso(v: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(v)) return null;
  const [y, m, d] = v.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return Number.isNaN(date.getTime()) ? null : date;
}

/** Accepts partial/loose typed input (8-digit ddmmyyyy, d/m/yyyy, d-m-yyyy, ...) and
 * auto-selects the matching date as soon as it's a complete, valid date — this is the
 * "type and it auto-selects" behavior requested, without needing a strict mask. */
function parseLoose(v: string): Date | null {
  const cleaned = v.trim();
  if (!cleaned) return null;

  // ISO yyyy-mm-dd (from the hidden native fallback / keyboard paste)
  const iso = parseIso(cleaned);
  if (iso) return iso;

  // dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy
  const sep = cleaned.match(/^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$/);
  if (sep) {
    const [, d, m, y] = sep;
    const date = new Date(Number(y), Number(m) - 1, Number(d));
    if (date.getMonth() === Number(m) - 1) return date;
  }

  // 8 digits typed straight through: ddmmyyyy
  const digits = cleaned.replace(/\D/g, "");
  if (digits.length === 8) {
    const d = Number(digits.slice(0, 2));
    const m = Number(digits.slice(2, 4));
    const y = Number(digits.slice(4, 8));
    const date = new Date(y, m - 1, d);
    if (date.getMonth() === m - 1) return date;
  }

  return null;
}

function formatDisplay(d: Date) {
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
}

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export function DatePicker({
  name,
  value,
  defaultValue,
  onChange,
  required,
  min,
  max,
  placeholder = "dd/mm/yyyy",
  className = "",
}: {
  name?: string;
  value?: string; // controlled, ISO yyyy-mm-dd
  defaultValue?: string; // uncontrolled, ISO yyyy-mm-dd
  onChange?: (isoValue: string) => void;
  required?: boolean;
  min?: string;
  max?: string;
  placeholder?: string;
  className?: string;
}) {
  const isControlled = value !== undefined;
  const [internalIso, setInternalIso] = useState(defaultValue || "");
  const iso = isControlled ? value : internalIso;
  const selected = iso ? parseIso(iso) : null;

  const [text, setText] = useState(selected ? formatDisplay(selected) : "");
  const [open, setOpen] = useState(false);
  const [viewMonth, setViewMonth] = useState(() => selected ?? new Date());
  const containerRef = useRef<HTMLDivElement>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const [popoverStyle, setPopoverStyle] = useState<{ top: number; left: number } | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!open) return;
    function position() {
      const el = containerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const popoverWidth = 288; // w-72
      const popoverHeight = 340;
      let left = rect.left;
      let top = rect.bottom + 8;
      // Keep the popover inside the viewport regardless of the parent's overflow/clip settings.
      if (left + popoverWidth > window.innerWidth - 8) left = window.innerWidth - popoverWidth - 8;
      if (left < 8) left = 8;
      if (top + popoverHeight > window.innerHeight - 8) top = rect.top - popoverHeight - 8;
      setPopoverStyle({ top, left });
    }
    position();
    window.addEventListener("resize", position);
    window.addEventListener("scroll", position, true);
    return () => {
      window.removeEventListener("resize", position);
      window.removeEventListener("scroll", position, true);
    };
  }, [open, viewMonth]);

  useEffect(() => {
    const next = iso ? parseIso(iso) : null;
    setText(next ? formatDisplay(next) : "");
    if (next) setViewMonth(next);
  }, [iso]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      const target = e.target as Node;
      if (containerRef.current?.contains(target)) return;
      if (popoverRef.current?.contains(target)) return;
      setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  function commit(date: Date) {
    const nextIso = toIso(date);
    if (!isControlled) setInternalIso(nextIso);
    setText(formatDisplay(date));
    setViewMonth(date);
    onChange?.(nextIso);
  }

  function handleTextChange(v: string) {
    setText(v);
    const parsed = parseLoose(v);
    if (parsed) {
      // Auto-select as soon as a complete valid date has been typed.
      const nextIso = toIso(parsed);
      if (!isControlled) setInternalIso(nextIso);
      setViewMonth(parsed);
      onChange?.(nextIso);
    } else if (!isControlled) {
      setInternalIso("");
      onChange?.("");
    }
  }

  const minDate = min ? parseIso(min) : null;
  const maxDate = max ? parseIso(max) : null;

  const firstOfMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth(), 1);
  const startWeekday = firstOfMonth.getDay();
  const daysInMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 0).getDate();
  const cells: (Date | null)[] = [];
  for (let i = 0; i < startWeekday; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(viewMonth.getFullYear(), viewMonth.getMonth(), d));

  const todayIso = toIso(new Date());

  return (
    <div ref={containerRef} className="relative">
      {name && <input type="hidden" name={name} value={iso || ""} required={required} />}
      <div className={`flex items-center gap-2 ${className}`}>
        <input
          type="text"
          value={text}
          onChange={(e) => handleTextChange(e.target.value)}
          onFocus={() => setOpen(true)}
          placeholder={placeholder}
          className="w-full bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400"
        />
        <button type="button" onClick={() => setOpen((v) => !v)} className="text-slate-400 hover:text-indigo-600" tabIndex={-1}>
          <CalendarIcon size={16} />
        </button>
      </div>

      {open &&
        mounted &&
        popoverStyle &&
        createPortal(
          <div
            ref={popoverRef}
            style={{ position: "fixed", top: popoverStyle.top, left: popoverStyle.left }}
            className="z-[100] w-72 rounded-xl border border-slate-200 bg-white p-3 shadow-xl"
          >
            <div className="mb-2 flex items-center justify-between">
              <button
                type="button"
                onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1))}
                className="rounded-lg p-1 text-slate-500 hover:bg-slate-100"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm font-semibold text-slate-800">
                {viewMonth.toLocaleString("default", { month: "long", year: "numeric" })}
              </span>
              <button
                type="button"
                onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1))}
                className="rounded-lg p-1 text-slate-500 hover:bg-slate-100"
              >
                <ChevronRight size={16} />
              </button>
            </div>

            <div className="mb-1 grid grid-cols-7 text-center text-[11px] font-medium text-slate-400">
              {WEEKDAYS.map((w) => (
                <span key={w}>{w}</span>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-1">
              {cells.map((d, i) => {
                if (!d) return <span key={i} />;
                const dIso = toIso(d);
                const isSelected = iso === dIso;
                const isToday = todayIso === dIso;
                const disabled = (minDate && d < minDate) || (maxDate && d > maxDate);
                return (
                  <button
                    key={i}
                    type="button"
                    disabled={!!disabled}
                    onClick={() => {
                      commit(d);
                      setOpen(false);
                    }}
                    className={`aspect-square rounded-lg text-xs font-medium transition-colors ${
                      isSelected
                        ? "bg-indigo-600 text-white"
                        : isToday
                          ? "bg-indigo-50 text-indigo-600"
                          : "text-slate-700 hover:bg-slate-100"
                    } ${disabled ? "cursor-not-allowed opacity-30 hover:bg-transparent" : ""}`}
                  >
                    {d.getDate()}
                  </button>
                );
              })}
            </div>

            <button
              type="button"
              onClick={() => {
                commit(new Date());
                setOpen(false);
              }}
              className="mt-2 w-full rounded-lg py-1.5 text-center text-xs font-medium text-indigo-600 hover:bg-indigo-50"
            >
              Today
            </button>
          </div>,
          document.body
        )}
    </div>
  );
}
