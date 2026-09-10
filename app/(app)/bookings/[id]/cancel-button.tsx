"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { cancelBookingAction } from "@/lib/actions/booking-actions";
import { Button } from "@/components/ui/button";

export function CancelButton({ bookingId }: { bookingId: string }) {
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const router = useRouter();

  return (
    <div className="space-y-2">
      {error && <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      <Button
        variant="danger"
        disabled={pending}
        onClick={() => {
          if (!confirm("Cancel this booking?")) return;
          startTransition(async () => {
            setError(null);
            const result = await cancelBookingAction(bookingId);
            if (!result.ok) {
              setError(result.error.message);
              return;
            }
            router.refresh();
          });
        }}
      >
        {pending ? "Cancelling..." : "Cancel Booking"}
      </Button>
    </div>
  );
}
