"use client";

import { useTransition } from "react";
import { deleteExpenseAction } from "@/lib/actions/ops-actions";

export function DeleteExpenseButton({ id }: { id: string }) {
  const [pending, startTransition] = useTransition();

  return (
    <button
      disabled={pending}
      onClick={() => {
        if (confirm("Delete this expense record?")) {
          startTransition(async () => { await deleteExpenseAction(id); });
        }
      }}
      className="text-xs font-medium text-rose-600 hover:underline disabled:opacity-50"
    >
      Delete
    </button>
  );
}
