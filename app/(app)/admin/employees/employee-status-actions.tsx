"use client";

import { useTransition } from "react";
import { setEmployeeStatusAction } from "@/lib/actions/master-data-actions";
import type { UserStatus } from "@/lib/types";

export function EmployeeStatusActions({ id, status }: { id: string; status: UserStatus }) {
  const [pending, startTransition] = useTransition();

  if (status === "ACTIVE") {
    return (
      <button
        disabled={pending}
        onClick={() => startTransition(() => setEmployeeStatusAction(id, "SUSPENDED"))}
        className="text-xs font-medium text-rose-600 hover:underline"
      >
        Suspend
      </button>
    );
  }

  if (status === "SUSPENDED") {
    return (
      <button
        disabled={pending}
        onClick={() => startTransition(() => setEmployeeStatusAction(id, "ACTIVE"))}
        className="text-xs font-medium text-emerald-600 hover:underline"
      >
        Activate
      </button>
    );
  }

  return <span className="text-xs text-slate-300">—</span>;
}
