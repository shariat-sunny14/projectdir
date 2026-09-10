"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { changeBookingVehicleAction } from "@/lib/actions/booking-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { Vehicle } from "@/lib/types";

const REASONS = [
  "Vehicle required for another booking",
  "Requested vehicle unavailable",
  "Vehicle under maintenance",
  "Higher passenger capacity required",
  "Emergency assignment",
  "Other",
];

export function ChangeVehiclePanel({
  bookingId,
  currentVehicleId,
  vehicles,
}: {
  bookingId: string;
  currentVehicleId: string | null;
  vehicles: Vehicle[];
}) {
  const [open, setOpen] = useState(false);
  const [vehicleId, setVehicleId] = useState("");
  const [reason, setReason] = useState(REASONS[0]);
  const [otherReason, setOtherReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  function submit() {
    setError(null);
    const finalReason = reason === "Other" ? otherReason : reason;
    startTransition(async () => {
      const result = await changeBookingVehicleAction(bookingId, vehicleId, finalReason);
      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      setOpen(false);
      router.refresh();
    });
  }

  if (!open) {
    return (
      <button onClick={() => setOpen(true)} className="text-xs font-medium text-indigo-600 hover:underline">
        Change Vehicle
      </button>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-slate-200 p-3">
      {error && <div className="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</div>}
      <Field label="New Vehicle" required>
        <select value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} className={inputClass}>
          <option value="">Select vehicle</option>
          {vehicles
            .filter((v) => v.id !== currentVehicleId && v.status !== "INACTIVE")
            .map((v) => (
              <option key={v.id} value={v.id}>
                {v.registrationNumber} — {v.vehicleName}
              </option>
            ))}
        </select>
      </Field>
      <Field label="Change Reason" required>
        <select value={reason} onChange={(e) => setReason(e.target.value)} className={inputClass}>
          {REASONS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </Field>
      {reason === "Other" && (
        <Field label="Specify Reason" required>
          <input value={otherReason} onChange={(e) => setOtherReason(e.target.value)} className={inputClass} />
        </Field>
      )}
      <div className="flex gap-2">
        <Button
          disabled={pending || !vehicleId || (reason === "Other" && !otherReason)}
          onClick={submit}
        >
          {pending ? "Saving..." : "Confirm Change"}
        </Button>
        <Button variant="secondary" onClick={() => setOpen(false)}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
