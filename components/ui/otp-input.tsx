"use client";

import { useRef } from "react";

/** 6 auto-advancing digit boxes with paste support — the standard OTP UX pattern. */
export function OtpInput({ value, onChange, length = 6, autoFocus = true }: { value: string; onChange: (v: string) => void; length?: number; autoFocus?: boolean }) {
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);
  const digits = value.split("").concat(Array(length).fill("")).slice(0, length);

  function setDigit(index: number, digit: string) {
    const next = digits.slice();
    next[index] = digit;
    onChange(next.join("").replace(/\s/g, ""));
  }

  function handleChange(index: number, raw: string) {
    const cleaned = raw.replace(/\D/g, "");
    if (!cleaned) {
      setDigit(index, "");
      return;
    }
    if (cleaned.length > 1) {
      // Fast path for pasting the whole code into one box.
      const next = digits.slice();
      for (let i = 0; i < cleaned.length && index + i < length; i++) next[index + i] = cleaned[i];
      onChange(next.join("").slice(0, length));
      const focusIndex = Math.min(index + cleaned.length, length - 1);
      inputsRef.current[focusIndex]?.focus();
      return;
    }
    setDigit(index, cleaned);
    if (index < length - 1) inputsRef.current[index + 1]?.focus();
  }

  function handleKeyDown(index: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
    if (e.key === "ArrowLeft" && index > 0) inputsRef.current[index - 1]?.focus();
    if (e.key === "ArrowRight" && index < length - 1) inputsRef.current[index + 1]?.focus();
  }

  return (
    <div className="flex justify-center gap-2">
      {digits.map((d, i) => (
        <input
          key={i}
          ref={(el) => {
            inputsRef.current[i] = el;
          }}
          autoFocus={autoFocus && i === 0}
          inputMode="numeric"
          maxLength={length}
          value={d}
          onChange={(e) => handleChange(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          className="h-12 w-11 rounded-xl border border-slate-200 bg-white text-center text-lg font-semibold text-slate-900 shadow-sm transition-colors focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100 sm:h-14 sm:w-12"
        />
      ))}
    </div>
  );
}
