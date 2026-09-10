"use client";

import { useState } from "react";
import { Plus, Pencil, X } from "lucide-react";
import { saveDriverAction } from "@/lib/actions/master-data-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import type { Driver, Vehicle } from "@/lib/types";

const STATUSES = ["AVAILABLE", "ON_TRIP", "OFF_DUTY", "INACTIVE"];

export function DriverForm({
  mode,
  driver,
  vehicles,
}: {
  mode: "create" | "edit";
  driver?: Driver;
  vehicles: Vehicle[];
}) {
  const [open, setOpen] = useState(false);

  return (
    <>
      {mode === "create" ? (
        <Button onClick={() => setOpen(true)}>
          <Plus size={16} /> Add Driver
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
              <h3 className="text-lg font-semibold text-slate-900">{mode === "create" ? "Add Driver" : "Edit Driver"}</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>

            <form
              action={async (fd) => {
                await saveDriverAction(fd);
                setOpen(false);
              }}
              className="space-y-4"
            >
              {driver && <input type="hidden" name="id" value={driver.id} />}

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Driver Name" required>
                  <input name="driverName" required defaultValue={driver?.driverName} className={inputClass} />
                </Field>
                <Field label="Phone" required>
                  <input name="phone" required defaultValue={driver?.phone} className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Email">
                  <input name="email" type="email" defaultValue={driver?.email} className={inputClass} />
                </Field>
                <Field label="Emergency Contact">
                  <input name="emergencyContact" defaultValue={driver?.emergencyContact} className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Field label="License Number" required>
                  <input name="licenseNumber" required defaultValue={driver?.licenseNumber} className={inputClass} />
                </Field>
                <Field label="License Type">
                  <input name="licenseType" defaultValue={driver?.licenseType} className={inputClass} />
                </Field>
                <Field label="License Expiry Date" required>
                  <DatePicker
                    name="licenseExpiryDate"
                    required
                    defaultValue={driver?.licenseExpiryDate}
                    className={inputClass}
                  />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Joining Date">
                  <DatePicker name="joiningDate" defaultValue={driver?.joiningDate} className={inputClass} />
                </Field>
                <Field label="Assigned Vehicle">
                  <select name="assignedVehicleId" defaultValue={driver?.assignedVehicleId || ""} className={inputClass}>
                    <option value="">Unassigned</option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.registrationNumber} — {v.vehicleName}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <Field label="Address">
                <textarea name="address" defaultValue={driver?.address} className={inputClass} rows={2} />
              </Field>

              <Field label="Status">
                <select name="status" defaultValue={driver?.status || "AVAILABLE"} className={inputClass}>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {s.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
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
