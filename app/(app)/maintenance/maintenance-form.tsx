"use client";

import { useState, useTransition } from "react";
import { Plus, X, AlertTriangle } from "lucide-react";
import { addMaintenanceAction } from "@/lib/actions/ops-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import type { Vehicle } from "@/lib/types";

const SERVICE_TYPES = [
  "General Service",
  "Engine Oil",
  "Brake",
  "Battery",
  "AC",
  "Tyre",
  "Engine",
  "Electrical",
  "Repair",
  "Other",
];

export function MaintenanceForm({ vehicles, isDriver = false }: { vehicles: Vehicle[]; isDriver?: boolean }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [vehicleId, setVehicleId] = useState("");
  const [currentKm, setCurrentKm] = useState<number | "">("");
  const [invoiceNumber, setInvoiceNumber] = useState("");

  function openModal() {
    setOpen(true);
    setVehicleId("");
    setCurrentKm("");
    // Auto-generate a suggested invoice number — still editable before saving.
    const stamp = new Date();
    setInvoiceNumber(
      `INV-${stamp.getFullYear()}${String(stamp.getMonth() + 1).padStart(2, "0")}${String(stamp.getDate()).padStart(2, "0")}-${String(
        stamp.getHours()
      ).padStart(2, "0")}${String(stamp.getMinutes()).padStart(2, "0")}${String(stamp.getSeconds()).padStart(2, "0")}`
    );
  }

  function handleVehicleChange(id: string) {
    setVehicleId(id);
    const v = vehicles.find((veh) => veh.id === id);
    setCurrentKm(v ? v.currentKm : "");
  }

  function submit(fd: FormData) {
    setError(null);
    startTransition(async () => {
      const result = await addMaintenanceAction(fd);
      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      if (result.data.conflictWarning) {
        setWarning(
          "This vehicle has an approved booking overlapping the maintenance window. The booking was NOT auto-cancelled — please resolve it manually."
        );
        return;
      }
      setOpen(false);
    });
  }

  return (
    <>
      <Button onClick={openModal}>
        <Plus size={16} /> {isDriver ? "Submit Service Entry" : "Add Service Record"}
      </Button>

      {warning && (
        <div className="fixed inset-x-0 top-4 z-[60] mx-auto flex w-fit items-center gap-2 rounded-lg bg-amber-50 px-4 py-2 text-sm text-amber-800 shadow-lg">
          <AlertTriangle size={16} />
          {warning}
          <button onClick={() => { setWarning(null); setOpen(false); }} className="ml-2 font-medium underline">
            Dismiss
          </button>
        </div>
      )}

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">{isDriver ? "Submit Service Entry" : "Add Service Record"}</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>

            {error && <div className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

            <form action={submit} className="space-y-4">
              <Field label="Vehicle" required>
                <select name="vehicleId" required className={inputClass} value={vehicleId} onChange={(e) => handleVehicleChange(e.target.value)}>
                  <option value="" disabled>
                    Select vehicle
                  </option>
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.registrationNumber} — {v.vehicleName}
                    </option>
                  ))}
                </select>
              </Field>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Service Type" required>
                  <select name="serviceType" required className={inputClass} defaultValue="">
                    <option value="" disabled>
                      Select
                    </option>
                    {SERVICE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Service Date" required>
                  <DatePicker name="serviceDate" required className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Current KM">
                  <input
                    name="currentKm"
                    type="number"
                    className={inputClass}
                    value={currentKm}
                    onChange={(e) => setCurrentKm(e.target.value === "" ? "" : Number(e.target.value))}
                  />
                </Field>
                <Field label="Invoice Number">
                  <input name="invoiceNumber" className={inputClass} value={invoiceNumber} onChange={(e) => setInvoiceNumber(e.target.value)} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Workshop">
                  <input name="workshop" className={inputClass} />
                </Field>
                <Field label="Mechanic">
                  <input name="mechanic" className={inputClass} />
                </Field>
              </div>

              <Field label="Description">
                <textarea name="description" className={inputClass} rows={2} />
              </Field>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Field label="Parts Cost (BDT)">
                  <input name="partsCost" type="number" defaultValue={0} className={inputClass} />
                </Field>
                <Field label="Labour Cost (BDT)">
                  <input name="labourCost" type="number" defaultValue={0} className={inputClass} />
                </Field>
                <Field label="Other Cost (BDT)">
                  <input name="otherCost" type="number" defaultValue={0} className={inputClass} />
                </Field>
              </div>
              <p className="text-xs text-slate-400">Total cost is calculated automatically as Parts + Labour + Other.</p>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Next Service Date">
                  <DatePicker name="nextServiceDate" className={inputClass} />
                </Field>
                <Field label="Next Service KM">
                  <input name="nextServiceKm" type="number" className={inputClass} />
                </Field>
              </div>

              {!isDriver && (
                <Field label="Status">
                  <select name="status" className={inputClass} defaultValue="OPEN">
                    <option value="OPEN">Open (vehicle goes to Maintenance)</option>
                    <option value="COMPLETED">Completed</option>
                  </select>
                </Field>
              )}

              <Field label="Remarks">
                <textarea name="remarks" className={inputClass} rows={2} />
              </Field>

              <Field label="Supporting Document (invoice/receipt — JPG, PNG or PDF)">
                <input name="document" type="file" accept=".jpg,.jpeg,.png,.pdf" className={`${inputClass} py-1.5`} />
              </Field>

              {isDriver && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  This entry will be sent to an admin for approval before it affects the vehicle&apos;s status.
                </p>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={pending}>
                  {pending ? "Saving..." : isDriver ? "Submit for Approval" : "Save"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
