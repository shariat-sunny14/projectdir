"use client";

import { useState } from "react";
import { Plus, Pencil, X } from "lucide-react";
import { saveVehicleAction } from "@/lib/actions/master-data-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import type { Vehicle, Department } from "@/lib/types";

const VEHICLE_TYPES = ["Sedan", "SUV", "Microbus", "Bus", "Pickup", "Van", "Other"];
const FUEL_TYPES = ["Petrol", "Octane", "Diesel", "CNG", "Hybrid", "Electric"];
const STATUSES = ["AVAILABLE", "BOOKED", "ON_TRIP", "MAINTENANCE", "INACTIVE"];

export function VehicleForm({
  mode,
  vehicle,
  departments,
}: {
  mode: "create" | "edit";
  vehicle?: Vehicle;
  departments: Department[];
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {mode === "create" ? (
        <Button onClick={() => setOpen(true)}>
          <Plus size={16} /> Add Vehicle
        </Button>
      ) : (
        <button onClick={() => setOpen(true)} className="text-slate-400 hover:text-indigo-600" aria-label="Edit">
          <Pencil size={16} />
        </button>
      )}

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">{mode === "create" ? "Add Vehicle" : "Edit Vehicle"}</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>

            <form
              action={async (fd) => {
                await saveVehicleAction(fd);
                setOpen(false);
              }}
              className="space-y-4"
            >
              {vehicle && <input type="hidden" name="id" value={vehicle.id} />}

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Registration Number" required>
                  <input name="registrationNumber" required defaultValue={vehicle?.registrationNumber} className={inputClass} />
                </Field>
                <Field label="Vehicle Name" required>
                  <input name="vehicleName" required defaultValue={vehicle?.vehicleName} className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Field label="Brand">
                  <input name="brand" defaultValue={vehicle?.brand} className={inputClass} />
                </Field>
                <Field label="Model">
                  <input name="model" defaultValue={vehicle?.model} className={inputClass} />
                </Field>
                <Field label="Model Year">
                  <input name="modelYear" type="number" defaultValue={vehicle?.modelYear} className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Field label="Vehicle Type" required>
                  <select name="vehicleType" required defaultValue={vehicle?.vehicleType || ""} className={inputClass}>
                    <option value="" disabled>
                      Select
                    </option>
                    {VEHICLE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Fuel Type" required>
                  <select name="fuelType" required defaultValue={vehicle?.fuelType || ""} className={inputClass}>
                    <option value="" disabled>
                      Select
                    </option>
                    {FUEL_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Seating Capacity">
                  <input name="seatingCapacity" type="number" defaultValue={vehicle?.seatingCapacity} className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Field label="Color">
                  <input name="color" defaultValue={vehicle?.color} className={inputClass} />
                </Field>
                <Field label="Current KM">
                  <input name="currentKm" type="number" defaultValue={vehicle?.currentKm ?? 0} className={inputClass} />
                </Field>
                <Field label="Assigned Department">
                  <select name="assignedDepartmentId" defaultValue={vehicle?.assignedDepartmentId || ""} className={inputClass}>
                    <option value="">Unassigned</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Field label="Insurance Expiry">
                  <DatePicker name="insuranceExpiry" defaultValue={vehicle?.insuranceExpiry} className={inputClass} />
                </Field>
                <Field label="Fitness Expiry">
                  <DatePicker name="fitnessExpiry" defaultValue={vehicle?.fitnessExpiry} className={inputClass} />
                </Field>
                <Field label="Tax Token Expiry">
                  <DatePicker name="taxTokenExpiry" defaultValue={vehicle?.taxTokenExpiry} className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Purchase Date">
                  <DatePicker name="purchaseDate" defaultValue={vehicle?.purchaseDate} className={inputClass} />
                </Field>
                <Field label="Purchase Price (BDT)">
                  <input name="purchasePrice" type="number" defaultValue={vehicle?.purchasePrice} className={inputClass} />
                </Field>
              </div>

              <Field label="Status">
                <select name="status" defaultValue={vehicle?.status || "AVAILABLE"} className={inputClass}>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </Field>

              <Field label="Notes">
                <textarea name="notes" defaultValue={vehicle?.notes} className={inputClass} rows={2} />
              </Field>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">Save</Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
