"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { Car, CheckCircle2, Loader2 } from "lucide-react";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import { TimePicker } from "@/components/ui/time-picker";
import { LocationSearchInput } from "@/components/ui/location-search-input";
import { MapView } from "@/components/ui/map-view";
import { createBookingAction } from "@/lib/actions/booking-actions";
import type { Vehicle, GeoLocation } from "@/lib/types";

interface TripDetails {
  startDate: string;
  startTime: string;
  endDate: string;
  endTime: string;
  purpose: string;
  passengerCount: string;
  remarks: string;
}

const EMPTY: TripDetails = {
  startDate: "",
  startTime: "",
  endDate: "",
  endTime: "",
  purpose: "",
  passengerCount: "",
  remarks: "",
};

const STEPS = ["Trip Details", "Available Vehicles", "Summary", "Confirmation"];

export function BookingWizard({ employeeName, departmentName }: { employeeName: string; departmentName: string }) {
  const [step, setStep] = useState(0);
  const [trip, setTrip] = useState<TripDetails>(EMPTY);
  const [pickup, setPickup] = useState<GeoLocation | null>(null);
  const [destination, setDestination] = useState<GeoLocation | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loadingVehicles, setLoadingVehicles] = useState(false);
  const [vehicleError, setVehicleError] = useState<string | null>(null);
  const [selectedVehicleId, setSelectedVehicleId] = useState<string | null>(null);
  const [tripError, setTripError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  async function fetchAvailability() {
    setTripError(null);

    if (!trip.startDate || !trip.startTime || !trip.endDate || !trip.endTime || !trip.purpose) {
      setTripError("Please fill in all required fields.");
      return;
    }
    if (!pickup || !destination) {
      setTripError("Search and select both a pickup and a destination location from the suggestions.");
      return;
    }
    const start = `${trip.startDate}T${trip.startTime}:00`;
    const end = `${trip.endDate}T${trip.endTime}:00`;
    if (new Date(start) >= new Date(end)) {
      setTripError("End time must be after start time.");
      return;
    }

    setLoadingVehicles(true);
    setVehicleError(null);
    try {
      const res = await fetch(`/api/bookings/available-vehicles?start=${encodeURIComponent(start)}&end=${encodeURIComponent(end)}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Failed to load available vehicles.");
      setVehicles(data.vehicles);
      setStep(1);
    } catch (err) {
      setVehicleError(err instanceof Error ? err.message : "Failed to load available vehicles.");
    } finally {
      setLoadingVehicles(false);
    }
  }

  function submit() {
    setSubmitError(null);
    if (!pickup || !destination) {
      setSubmitError("Pickup and destination locations are required.");
      return;
    }
    const fd = new FormData();
    Object.entries(trip).forEach(([k, v]) => fd.set(k, v));
    fd.set("pickupLocationDetails", JSON.stringify(pickup));
    fd.set("destinationLocationDetails", JSON.stringify(destination));
    fd.set("requestedVehicleId", selectedVehicleId || "");
    startTransition(async () => {
      const result = await createBookingAction(fd);
      if (!result.ok) {
        setSubmitError(result.error.message);
        // A conflict means someone else grabbed this vehicle since we checked — send them back to re-pick.
        if (result.error.code === "ERR_VEHICLE_CONFLICT") setStep(1);
        return;
      }
      router.push("/bookings?created=1");
    });
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">
      {/* Stepper */}
      <div className="mb-6 flex items-center gap-2">
        {STEPS.map((label, i) => (
          <div key={label} className="flex flex-1 items-center gap-2">
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                i <= step ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-400"
              }`}
            >
              {i + 1}
            </div>
            <span className={`hidden text-xs font-medium sm:block ${i <= step ? "text-slate-700" : "text-slate-400"}`}>{label}</span>
            {i < STEPS.length - 1 && <div className={`h-px flex-1 ${i < step ? "bg-indigo-600" : "bg-slate-200"}`} />}
          </div>
        ))}
      </div>

      {step === 0 && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Booking Start Date" required>
              <DatePicker required className={inputClass} value={trip.startDate} onChange={(iso) => setTrip({ ...trip, startDate: iso })} />
            </Field>
            <Field label="Booking Start Time" required>
              <TimePicker required className={inputClass} value={trip.startTime} onChange={(v) => setTrip({ ...trip, startTime: v })} />
            </Field>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Booking End Date" required>
              <DatePicker required className={inputClass} value={trip.endDate} onChange={(iso) => setTrip({ ...trip, endDate: iso })} />
            </Field>
            <Field label="Booking End Time" required>
              <TimePicker required className={inputClass} value={trip.endTime} onChange={(v) => setTrip({ ...trip, endTime: v })} />
            </Field>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Pickup Location" required>
              <LocationSearchInput value={pickup} onChange={setPickup} placeholder="Where should the driver pick you up?" />
            </Field>
            <Field label="Destination Location" required>
              <LocationSearchInput value={destination} onChange={setDestination} placeholder="Where are you going?" />
            </Field>
          </div>
          {pickup && destination && (
            <MapView
              height="200px"
              markers={[
                { id: "pickup", lat: pickup.lat, lng: pickup.lng, color: "#059669", label: "A" },
                { id: "dest", lat: destination.lat, lng: destination.lng, color: "#e11d48", label: "B" },
              ]}
              path={[pickup, destination]}
            />
          )}
          <Field label="Purpose" required>
            <input required className={inputClass} value={trip.purpose} onChange={(e) => setTrip({ ...trip, purpose: e.target.value })} />
          </Field>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="Passenger Count">
              <input type="number" min={1} className={inputClass} value={trip.passengerCount} onChange={(e) => setTrip({ ...trip, passengerCount: e.target.value })} />
            </Field>
            <Field label="Remarks">
              <input className={inputClass} value={trip.remarks} onChange={(e) => setTrip({ ...trip, remarks: e.target.value })} />
            </Field>
          </div>

          {tripError && <p className="text-sm text-rose-600">{tripError}</p>}

          <div className="flex justify-end">
            <Button onClick={fetchAvailability} disabled={loadingVehicles}>
              {loadingVehicles ? <Loader2 className="animate-spin" size={16} /> : null}
              Check Availability
            </Button>
          </div>
        </div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          {vehicleError && <p className="text-sm text-rose-600">{vehicleError}</p>}
          {vehicles.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">No vehicles are available for the selected time window.</p>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {vehicles.map((v) => (
                <button
                  key={v.id}
                  onClick={() => setSelectedVehicleId(v.id)}
                  className={`flex items-start gap-3 rounded-xl border p-4 text-left transition-colors ${
                    selectedVehicleId === v.id ? "border-indigo-600 bg-indigo-50" : "border-slate-200 hover:border-indigo-300"
                  }`}
                >
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600">
                    <Car size={18} />
                  </div>
                  <div>
                    <p className="font-medium text-slate-800">{v.vehicleName}</p>
                    <p className="text-xs text-slate-500">{v.registrationNumber}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      {v.vehicleType} · {v.fuelType} · {v.seatingCapacity ?? "—"} seats · {v.currentKm.toLocaleString()} km
                    </p>
                  </div>
                </button>
              ))}
            </div>
          )}

          <div className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep(0)}>
              Back
            </Button>
            <Button disabled={!selectedVehicleId} onClick={() => setStep(2)}>
              Continue
            </Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
            <SummaryRow label="Employee" value={employeeName} />
            <SummaryRow label="Department" value={departmentName} />
            <SummaryRow label="Start" value={`${trip.startDate} ${trip.startTime}`} />
            <SummaryRow label="End" value={`${trip.endDate} ${trip.endTime}`} />
            <SummaryRow label="Pickup" value={pickup?.name || "—"} />
            <SummaryRow label="Destination" value={destination?.name || "—"} />
            <SummaryRow label="Purpose" value={trip.purpose} />
            <SummaryRow label="Passengers" value={trip.passengerCount || "—"} />
            <SummaryRow
              label="Requested Vehicle"
              value={vehicles.find((v) => v.id === selectedVehicleId)?.vehicleName || "—"}
            />
          </dl>

          {pickup && destination && (
            <MapView
              height="220px"
              markers={[
                { id: "pickup", lat: pickup.lat, lng: pickup.lng, color: "#059669", label: "A", popupHtml: `<strong>Pickup</strong><br/>${pickup.name}` },
                { id: "dest", lat: destination.lat, lng: destination.lng, color: "#e11d48", label: "B", popupHtml: `<strong>Destination</strong><br/>${destination.name}` },
              ]}
              path={[pickup, destination]}
            />
          )}

          <div className="flex justify-between">
            <Button variant="secondary" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button onClick={() => setStep(3)}>Continue</Button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4 text-center">
          <CheckCircle2 className="mx-auto text-emerald-500" size={40} />
          <p className="text-slate-700">
            Ready to submit your booking request for <strong>{vehicles.find((v) => v.id === selectedVehicleId)?.vehicleName}</strong>?
          </p>
          <p className="text-xs text-slate-400">This will be sent to an admin for approval. The requested vehicle may change during review.</p>
          {submitError && <p className="text-sm text-rose-600">{submitError}</p>}
          <div className="flex justify-center gap-2">
            <Button variant="secondary" onClick={() => setStep(2)}>
              Back
            </Button>
            <Button onClick={submit} disabled={pending}>
              {pending ? "Submitting..." : "Confirm Booking"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs uppercase text-slate-400">{label}</dt>
      <dd className="font-medium text-slate-800">{value}</dd>
    </div>
  );
}
