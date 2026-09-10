"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { approveBookingAction, rejectBookingAction } from "@/lib/actions/booking-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { Vehicle, Driver } from "@/lib/types";

export function ApprovalPanel({
  bookingId,
  requestedVehicleId,
  vehicles,
  drivers,
}: {
  bookingId: string;
  requestedVehicleId: string;
  vehicles: Vehicle[];
  drivers: Driver[];
}) {
  const [vehicleId, setVehicleId] = useState(requestedVehicleId);
  const [driverId, setDriverId] = useState("");
  const [reason, setReason] = useState("");
  const [mode, setMode] = useState<"approve" | "reject">("approve");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  function submitApprove() {
    setError(null);
    startTransition(async () => {
      const result = await approveBookingAction(bookingId, vehicleId, driverId);
      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      router.refresh();
    });
  }

  function submitReject() {
    setError(null);
    startTransition(async () => {
      const result = await rejectBookingAction(bookingId, reason);
      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      router.refresh();
    });
  }

  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
      <h2 className="mb-3 font-semibold text-slate-900">Approval</h2>

      {error && <div className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

      <div className="mb-3 flex gap-2">
        <button
          onClick={() => setMode("approve")}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${mode === "approve" ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-600"}`}
        >
          Approve
        </button>
        <button
          onClick={() => setMode("reject")}
          className={`rounded-lg px-3 py-1.5 text-sm font-medium ${mode === "reject" ? "bg-rose-600 text-white" : "bg-slate-100 text-slate-600"}`}
        >
          Reject
        </button>
      </div>

      {mode === "approve" ? (
        <div className="space-y-3">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Vehicle" required>
              <select value={vehicleId} onChange={(e) => setVehicleId(e.target.value)} className={inputClass}>
                {vehicles
                  .filter((v) => v.status !== "INACTIVE")
                  .map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.registrationNumber} — {v.vehicleName}
                    </option>
                  ))}
              </select>
            </Field>
            <Field label="Driver" required>
              <select value={driverId} onChange={(e) => setDriverId(e.target.value)} className={inputClass}>
                <option value="">Select driver</option>
                {drivers
                  .filter((d) => d.status !== "INACTIVE")
                  .map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.driverName}
                    </option>
                  ))}
              </select>
            </Field>
          </div>
          <Button disabled={pending || !vehicleId || !driverId} onClick={submitApprove}>
            {pending ? "Approving..." : "Approve Booking"}
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <Field label="Rejection Reason" required>
            <input value={reason} onChange={(e) => setReason(e.target.value)} className={inputClass} />
          </Field>
          <Button variant="danger" disabled={pending || !reason} onClick={submitReject}>
            {pending ? "Rejecting..." : "Reject Booking"}
          </Button>
        </div>
      )}
    </section>
  );
}
