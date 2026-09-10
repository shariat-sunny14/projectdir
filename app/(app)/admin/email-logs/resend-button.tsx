"use client";

import { useState, useTransition } from "react";
import { RefreshCw } from "lucide-react";
import { resendEmailAction } from "@/lib/actions/email-log-actions";

export function ResendButton({ logId }: { logId: string }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  return (
    <div>
      <button
        disabled={pending}
        onClick={() =>
          startTransition(async () => {
            setError(null);
            const result = await resendEmailAction(logId);
            if (!result.ok) {
              setError(result.error.message);
              return;
            }
            setDone(true);
            setTimeout(() => setDone(false), 3000);
          })
        }
        className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:underline disabled:opacity-50"
      >
        <RefreshCw size={12} className={pending ? "animate-spin" : ""} />
        {pending ? "Resending..." : done ? "Resent!" : "Resend"}
      </button>
      {error && <p className="mt-0.5 text-xs text-rose-500">{error}</p>}
    </div>
  );
}
