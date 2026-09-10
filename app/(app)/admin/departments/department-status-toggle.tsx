"use client";

import { useTransition } from "react";
import { setDepartmentStatusAction } from "@/lib/actions/master-data-actions";

export function DepartmentStatusToggle({
  id,
  status,
  disabled,
}: {
  id: string;
  status: "ACTIVE" | "INACTIVE";
  disabled?: boolean;
}) {
  const [pending, startTransition] = useTransition();
  const next = status === "ACTIVE" ? "INACTIVE" : "ACTIVE";

  return (
    <button
      disabled={pending || disabled}
      title={disabled ? "Cannot deactivate: employees are assigned to this department" : undefined}
      onClick={() => startTransition(() => setDepartmentStatusAction(id, next))}
      className="text-xs font-medium text-slate-500 underline decoration-dotted hover:text-indigo-600 disabled:cursor-not-allowed disabled:text-slate-300"
    >
      {status === "ACTIVE" ? "Deactivate" : "Activate"}
    </button>
  );
}
