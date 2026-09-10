"use client";

import { useRef, useState } from "react";
import { Plus, Pencil, X } from "lucide-react";
import { saveDepartmentAction } from "@/lib/actions/master-data-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { Department } from "@/lib/types";

export function DepartmentForm({ mode, department }: { mode: "create" | "edit"; department?: Department }) {
  const [open, setOpen] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);

  return (
    <>
      {mode === "create" ? (
        <Button onClick={() => setOpen(true)}>
          <Plus size={16} /> Add Department
        </Button>
      ) : (
        <button onClick={() => setOpen(true)} className="text-slate-400 hover:text-indigo-600" aria-label="Edit">
          <Pencil size={16} />
        </button>
      )}

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">
                {mode === "create" ? "Add Department" : "Edit Department"}
              </h3>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>

            <form
              ref={formRef}
              action={async (fd) => {
                await saveDepartmentAction(fd);
                setOpen(false);
              }}
              className="space-y-4"
            >
              {department && <input type="hidden" name="id" value={department.id} />}

              <Field label="Department Code" required>
                <input name="code" required defaultValue={department?.code} className={inputClass} />
              </Field>
              <Field label="Department Name" required>
                <input name="name" required defaultValue={department?.name} className={inputClass} />
              </Field>
              <Field label="Manager">
                <input name="manager" defaultValue={department?.manager} className={inputClass} />
              </Field>
              <Field label="Description">
                <textarea name="description" defaultValue={department?.description} className={inputClass} rows={2} />
              </Field>
              <Field label="Status">
                <select name="status" defaultValue={department?.status || "ACTIVE"} className={inputClass}>
                  <option value="ACTIVE">Active</option>
                  <option value="INACTIVE">Inactive</option>
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
