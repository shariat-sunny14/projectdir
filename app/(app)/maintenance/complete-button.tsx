"use client";

import { useTransition } from "react";
import { completeMaintenanceAction } from "@/lib/actions/ops-actions";

export function CompleteMaintenanceButton({ id }: { id: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <button
      disabled={pending}
      onClick={() => startTransition(async () => { await completeMaintenanceAction(id); })}
      className="text-xs font-medium text-emerald-600 hover:underline disabled:opacity-50"
    >
      {pending ? "Saving..." : "Mark Completed"}
    </button>
  );
}
