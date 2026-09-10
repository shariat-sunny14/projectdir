"use client";

import { useState, useTransition } from "react";
import { approveMaintenanceEntryAction, rejectMaintenanceEntryAction } from "@/lib/actions/ops-actions";
import { Button } from "@/components/ui/button";

export function MaintenanceApprovalActions({ id }: { id: string }) {
  const [pending, startTransition] = useTransition();
  const [showReject, setShowReject] = useState(false);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  if (showReject) {
    return (
      <div className="flex flex-col gap-1">
        <input
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason"
          className="rounded-lg border border-slate-300 px-2 py-1 text-xs"
        />
        {error && <p className="text-xs text-rose-500">{error}</p>}
        <div className="flex gap-2">
          <Button
            variant="danger"
            disabled={pending || !reason}
            onClick={() =>
              startTransition(async () => {
                const result = await rejectMaintenanceEntryAction(id, reason);
                if (!result.ok) setError(result.error.message);
              })
            }
          >
            Confirm
          </Button>
          <Button variant="ghost" onClick={() => setShowReject(false)}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      {error && <p className="text-xs text-rose-500">{error}</p>}
      <div className="flex gap-2">
        <Button
          disabled={pending}
          onClick={() =>
            startTransition(async () => {
              const result = await approveMaintenanceEntryAction(id);
              if (!result.ok) setError(result.error.message);
            })
          }
        >
          Approve
        </Button>
        <Button variant="secondary" disabled={pending} onClick={() => setShowReject(true)}>
          Reject
        </Button>
      </div>
    </div>
  );
}
