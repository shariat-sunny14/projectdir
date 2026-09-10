"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { startTripAction, completeTripAction } from "@/lib/actions/trip-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { Booking, Trip } from "@/lib/types";

export function TripPanel({
  booking,
  trip,
  isDriver,
  vehicleCurrentKm,
}: {
  booking: Booking;
  trip: Trip | undefined;
  isDriver: boolean;
  vehicleCurrentKm?: number;
}) {
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  const [startingKm, setStartingKm] = useState(vehicleCurrentKm ?? 0);
  const [startLocation, setStartLocation] = useState(booking.pickupLocation);
  const [startRemarks, setStartRemarks] = useState("");

  const [endingKm, setEndingKm] = useState(trip?.startingKm ?? 0);
  const [endLocation, setEndLocation] = useState(booking.destinationLocation);
  const [endRemarks, setEndRemarks] = useState("");

  if (booking.status === "APPROVED" && !trip) {
    return (
      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
        <h2 className="mb-3 font-semibold text-slate-900">{isDriver ? "Start Your Trip" : "Start Trip"}</h2>
        {error && <div className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Field label="Starting KM">
            <input type="number" value={startingKm} onChange={(e) => setStartingKm(Number(e.target.value))} className={inputClass} />
          </Field>
          <Field label="Start Location">
            <input value={startLocation} onChange={(e) => setStartLocation(e.target.value)} className={inputClass} />
          </Field>
          <Field label="Driver Remarks">
            <input value={startRemarks} onChange={(e) => setStartRemarks(e.target.value)} className={inputClass} />
          </Field>
        </div>
        <div className="mt-3">
          <Button
            disabled={pending}
            onClick={() =>
              startTransition(async () => {
                setError(null);
                const result = await startTripAction(booking.id, startingKm, startLocation, startRemarks);
                if (!result.ok) {
                  setError(result.error.message);
                  return;
                }
                router.refresh();
              })
            }
          >
            {pending ? "Starting..." : "Start Trip"}
          </Button>
        </div>
      </section>
    );
  }

  if (booking.status === "ON_TRIP" && trip && trip.status === "RUNNING") {
    return (
      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
        <h2 className="mb-3 font-semibold text-slate-900">{isDriver ? "Complete Your Trip" : "Complete Trip"}</h2>
        <p className="mb-3 text-sm text-slate-500">Started {new Date(trip.actualStart).toLocaleString()} at {trip.startingKm.toLocaleString()} km.</p>
        {error && <div className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Field label="Ending KM" required>
            <input type="number" value={endingKm} onChange={(e) => setEndingKm(Number(e.target.value))} className={inputClass} />
          </Field>
          <Field label="End Location">
            <input value={endLocation} onChange={(e) => setEndLocation(e.target.value)} className={inputClass} />
          </Field>
          <Field label="Driver Remarks">
            <input value={endRemarks} onChange={(e) => setEndRemarks(e.target.value)} className={inputClass} />
          </Field>
        </div>
        <div className="mt-3">
          <Button
            disabled={pending}
            onClick={() =>
              startTransition(async () => {
                setError(null);
                const result = await completeTripAction(trip.id, booking.id, endingKm, endLocation, endRemarks);
                if (!result.ok) {
                  setError(result.error.message);
                  return;
                }
                router.refresh();
              })
            }
          >
            {pending ? "Completing..." : "Complete Trip"}
          </Button>
        </div>
      </section>
    );
  }

  if (booking.status === "COMPLETED" && trip) {
    return (
      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
        <h2 className="mb-3 font-semibold text-slate-900">Trip Summary</h2>
        <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
          <SummaryStat label="Starting KM" value={trip.startingKm.toLocaleString()} />
          <SummaryStat label="Ending KM" value={trip.endingKm?.toLocaleString() ?? "—"} />
          <SummaryStat label="Total KM" value={trip.totalKm?.toLocaleString() ?? "—"} />
          <SummaryStat label="Duration" value={trip.actualEnd ? `${Math.round((new Date(trip.actualEnd).getTime() - new Date(trip.actualStart).getTime()) / 60000)} min` : "—"} />
        </dl>
      </section>
    );
  }

  return null;
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase text-slate-400">{label}</dt>
      <dd className="font-semibold text-slate-800">{value}</dd>
    </div>
  );
}
