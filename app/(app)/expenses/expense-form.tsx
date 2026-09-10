"use client";

import { useState, useTransition } from "react";
import { Plus, X } from "lucide-react";
import { addExpenseAction } from "@/lib/actions/ops-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import { DatePicker } from "@/components/ui/date-picker";
import type { Vehicle, Booking } from "@/lib/types";

const CATEGORIES = ["FUEL", "TOLL", "TIP", "PARKING", "REPAIR", "SERVICE", "INSURANCE", "TAX", "OTHER"];
const PAYMENT_METHODS = ["CASH", "BANK", "DEBIT_CARD", "CREDIT_CARD", "BKASH", "NAGAD", "OTHER"];

export function ExpenseForm({ vehicles, bookings, isDriver = false }: { vehicles: Vehicle[]; bookings: Booking[]; isDriver?: boolean }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(fd: FormData) {
    setError(null);
    startTransition(async () => {
      const result = await addExpenseAction(fd);
      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      setOpen(false);
    });
  }

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        <Plus size={16} /> {isDriver ? "Submit Expense" : "Add Expense"}
      </Button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">{isDriver ? "Submit Expense" : "Add Expense"}</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>

            {error && <div className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

            <form action={submit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Vehicle" required>
                  <select name="vehicleId" required className={inputClass} defaultValue="">
                    <option value="" disabled>
                      Select vehicle
                    </option>
                    {vehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.registrationNumber}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Trip / Booking">
                  <select name="bookingId" className={inputClass} defaultValue="">
                    <option value="">None</option>
                    {bookings.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.id}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Expense Type" required>
                  <select name="category" required className={inputClass} defaultValue="">
                    <option value="" disabled>
                      Select
                    </option>
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Amount (BDT)" required>
                  <input name="amount" type="number" required className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Expense Date" required>
                  <DatePicker name="expenseDate" required className={inputClass} />
                </Field>
                <Field label="Payment Method" required>
                  <select name="paymentMethod" required className={inputClass} defaultValue="">
                    <option value="" disabled>
                      Select
                    </option>
                    {PAYMENT_METHODS.map((p) => (
                      <option key={p} value={p}>
                        {p.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <Field label="Location">
                <input name="location" className={inputClass} />
              </Field>
              <Field label="Description">
                <textarea name="description" className={inputClass} rows={2} />
              </Field>

              <Field label="Receipt (JPG, PNG or PDF)">
                <input name="document" type="file" accept=".jpg,.jpeg,.png,.pdf" className={`${inputClass} py-1.5`} />
              </Field>

              {isDriver && (
                <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
                  This expense will be sent to an admin for approval.
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
