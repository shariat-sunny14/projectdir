"use client";

import { useEffect, useRef, useState } from "react";
import { MapPin, Search, X, Loader2 } from "lucide-react";
import { searchLocationsAction } from "@/lib/actions/location-actions";
import { inputClass } from "@/components/ui/field";
import type { GeoLocation } from "@/lib/types";

/** Uber-style "search as you type, pick a suggestion" location picker (Feature #6).
 * Once a location is selected it renders as a confirmed card with a change (X) button
 * so pickup/destination can always be edited (requirement #9). */
export function LocationSearchInput({
  value,
  onChange,
  placeholder,
}: {
  value: GeoLocation | null;
  onChange: (loc: GeoLocation | null) => void;
  placeholder?: string;
}) {
  const [query, setQuery] = useState(value?.name ?? "");
  const [results, setResults] = useState<GeoLocation[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [seenValue, setSeenValue] = useState(value);
  if (value !== seenValue) {
    setSeenValue(value);
    setQuery(value?.name ?? "");
  }

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  function handleInput(v: string) {
    setQuery(v);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (v.trim().length < 3) {
      setResults([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    debounceRef.current = setTimeout(async () => {
      const res = await searchLocationsAction(v);
      setResults(res);
      setLoading(false);
      setOpen(true);
    }, 400);
  }

  function select(loc: GeoLocation) {
    onChange(loc);
    setQuery(loc.name);
    setOpen(false);
    setResults([]);
  }

  function clear() {
    onChange(null);
    setQuery("");
    setResults([]);
    setOpen(false);
  }

  if (value) {
    return (
      <div className="flex items-start gap-2 rounded-xl border border-emerald-200 bg-emerald-50/60 px-3.5 py-2.5">
        <MapPin size={16} className="mt-0.5 shrink-0 text-emerald-600" />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-slate-800">{value.name}</p>
          <p className="truncate text-xs text-slate-500">{value.address}</p>
        </div>
        <button
          type="button"
          onClick={clear}
          className="shrink-0 rounded-lg p-1 text-slate-400 transition-colors hover:bg-white hover:text-rose-500"
          aria-label="Change location"
        >
          <X size={15} />
        </button>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      <div className="relative">
        <Search size={15} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          className={`${inputClass} pl-9 pr-9`}
          value={query}
          placeholder={placeholder || "Search a place, address or landmark..."}
          onChange={(e) => handleInput(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          autoComplete="off"
        />
        {loading && <Loader2 size={15} className="absolute right-3.5 top-1/2 -translate-y-1/2 animate-spin text-slate-400" />}
      </div>

      {open && results.length > 0 && (
        <div className="absolute z-30 mt-1.5 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          {results.map((r, i) => (
            <button
              key={`${r.lat}-${r.lng}-${i}`}
              type="button"
              onClick={() => select(r)}
              className="flex w-full items-start gap-2.5 border-b border-slate-50 px-3.5 py-2.5 text-left last:border-0 hover:bg-indigo-50"
            >
              <MapPin size={15} className="mt-0.5 shrink-0 text-indigo-500" />
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-slate-800">{r.name}</p>
                <p className="truncate text-xs text-slate-500">{r.address}</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {open && !loading && query.trim().length >= 3 && results.length === 0 && (
        <div className="absolute z-30 mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-xs text-slate-400 shadow-lg">
          No matches yet — keep typing a more specific address.
        </div>
      )}
    </div>
  );
}
