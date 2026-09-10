"use client";

import { useState, useTransition } from "react";
import { approveUserAction, rejectUserAction } from "@/lib/actions/admin-actions";
import { Button } from "@/components/ui/button";
import type { User, Role } from "@/lib/types";

const ROLES: Role[] = ["EMPLOYEE", "DRIVER", "TRANSPORT_MANAGER", "ADMIN", "SUPER_ADMIN"];

export function ApprovalRow({ user, departmentName }: { user: User; departmentName: string }) {
  const [pending, startTransition] = useTransition();
  const [showReject, setShowReject] = useState(false);
  const [reason, setReason] = useState("");
  const [role, setRole] = useState<Role>(user.role);

  return (
    <div className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="font-medium text-slate-800">{user.fullName}</p>
        <p className="text-sm text-slate-500">
          {user.email} · {user.phone} · {departmentName} · {user.designation}
        </p>
      </div>

      {showReject ? (
        <div className="flex items-center gap-2">
          <input
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Rejection reason"
            className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
          />
          <Button
            variant="danger"
            disabled={pending || !reason}
            onClick={() => startTransition(() => rejectUserAction(user.id, reason))}
          >
            Confirm reject
          </Button>
          <Button variant="ghost" onClick={() => setShowReject(false)}>
            Cancel
          </Button>
        </div>
      ) : (
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as Role)}
            disabled={pending}
            className="rounded-lg border border-slate-300 px-2 py-1.5 text-xs text-slate-700"
            title="Role to assign on approval"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r.replaceAll("_", " ")}
              </option>
            ))}
          </select>
          <Button variant="secondary" disabled={pending} onClick={() => setShowReject(true)}>
            Reject
          </Button>
          <Button disabled={pending} onClick={() => startTransition(() => approveUserAction(user.id, role))}>
            Approve
          </Button>
        </div>
      )}
    </div>
  );
}
