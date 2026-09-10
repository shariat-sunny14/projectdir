"use client";

import { useState, useTransition } from "react";
import { Plus, X } from "lucide-react";
import { createEmployeeAction } from "@/lib/actions/master-data-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { Department, Role } from "@/lib/types";

const ROLES: Role[] = ["EMPLOYEE", "DRIVER", "TRANSPORT_MANAGER", "ADMIN", "SUPER_ADMIN"];

export function EmployeeCreateForm({ departments, canAssignAnyRole }: { departments: Department[]; canAssignAnyRole: boolean }) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(fd: FormData) {
    setError(null);
    startTransition(async () => {
      try {
        await createEmployeeAction(fd);
        setOpen(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not create the account.");
      }
    });
  }

  return (
    <>
      <Button onClick={() => setOpen(true)}>
        <Plus size={16} /> Add Employee
      </Button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Add Employee</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>

            {error && <div className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

            <form action={submit} className="space-y-4">
              <Field label="Full Name" required>
                <input name="fullName" required className={inputClass} />
              </Field>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Email" required>
                  <input name="email" type="email" required className={inputClass} />
                </Field>
                <Field label="Phone" required>
                  <input name="phone" required className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Employee ID">
                  <input name="employeeId" className={inputClass} />
                </Field>
                <Field label="Department">
                  <select name="departmentId" className={inputClass} defaultValue="">
                    <option value="">Unassigned</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Designation">
                  <input name="designation" className={inputClass} />
                </Field>
                <Field label="Role" required>
                  <select name="role" required className={inputClass} defaultValue="EMPLOYEE">
                    {ROLES.map((r) => (
                      <option key={r} value={r} disabled={!canAssignAnyRole && r !== "EMPLOYEE" && r !== "DRIVER"}>
                        {r.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <Field label="Temporary Password" required>
                <input name="password" type="text" required defaultValue="Passw0rd!" className={inputClass} />
                <p className="mt-1 text-xs text-slate-400">Share this with the employee — they should change it after first login.</p>
              </Field>

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={pending}>
                  {pending ? "Creating..." : "Create Account"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
