"use client";

import { useState, useTransition } from "react";
import { Pencil, X } from "lucide-react";
import { updateEmployeeAction } from "@/lib/actions/master-data-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { User, Department, Role, UserStatus } from "@/lib/types";

const ROLES: Role[] = ["EMPLOYEE", "DRIVER", "TRANSPORT_MANAGER", "ADMIN", "SUPER_ADMIN"];
const STATUSES: UserStatus[] = ["ACTIVE", "SUSPENDED"];

export function EmployeeEditForm({
  user,
  departments,
  canEditRole,
  isSelf,
}: {
  user: User;
  departments: Department[];
  canEditRole: boolean;
  isSelf: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function submit(fd: FormData) {
    setError(null);
    startTransition(async () => {
      try {
        await updateEmployeeAction(fd);
        setOpen(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Update failed.");
      }
    });
  }

  return (
    <>
      <button onClick={() => setOpen(true)} className="text-slate-400 hover:text-indigo-600" aria-label="Edit employee">
        <Pencil size={16} />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">Edit {user.fullName}</h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>

            {error && <div className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

            <form action={submit} className="space-y-4">
              <input type="hidden" name="id" value={user.id} />

              <Field label="Full Name" required>
                <input name="fullName" required defaultValue={user.fullName} className={inputClass} />
              </Field>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Email" required>
                  <input name="email" type="email" required defaultValue={user.email} className={inputClass} />
                </Field>
                <Field label="Phone" required>
                  <input name="phone" required defaultValue={user.phone} className={inputClass} />
                </Field>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Employee ID">
                  <input name="employeeId" defaultValue={user.employeeId} className={inputClass} />
                </Field>
                <Field label="Department">
                  <select name="departmentId" defaultValue={user.departmentId || ""} className={inputClass}>
                    <option value="">Unassigned</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>

              <Field label="Designation">
                <input name="designation" defaultValue={user.designation} className={inputClass} />
              </Field>

              <Field label="Address">
                <textarea name="address" defaultValue={user.address} className={inputClass} rows={2} />
              </Field>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <Field label="Role" required>
                  <select
                    name="role"
                    defaultValue={user.role}
                    disabled={!canEditRole || isSelf}
                    className={`${inputClass} disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400`}
                  >
                    {ROLES.map((r) => (
                      <option key={r} value={r}>
                        {r.replaceAll("_", " ")}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Status" required>
                  <select
                    name="status"
                    defaultValue={user.status === "ACTIVE" || user.status === "SUSPENDED" ? user.status : "ACTIVE"}
                    disabled={isSelf}
                    className={`${inputClass} disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400`}
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
              {!canEditRole && <p className="text-xs text-slate-400">Only Super Admin / Admin can change roles.</p>}
              {isSelf && <p className="text-xs text-slate-400">You can&apos;t change your own role or status.</p>}

              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="secondary" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={pending}>
                  {pending ? "Saving..." : "Save"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
