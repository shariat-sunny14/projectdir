"use server";

import { getSession } from "@/lib/auth/session";
import { canApproveBookings } from "@/lib/permissions";
import {
  recordVehicleLocation,
  getActiveTrackedVehicles,
  getTripTrackingStatus,
  getTripLocationHistory,
} from "@/lib/services/tracking-service";
import { AppError, runAction, type ActionResult } from "@/lib/errors";

/** Called every few seconds from the driver's browser while a trip is RUNNING. */
export async function pingVehicleLocationAction(tripId: string, lat: number, lng: number): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await getSession();
    if (!session) throw new AppError("ERR_FORBIDDEN", "Not authenticated.");
    await recordVehicleLocation({ tripId, lat, lng, actorUserId: session.userId });
    return null;
  });
}

/** Polled by the admin/manager "Live Fleet" map. */
export async function getActiveTrackingAction() {
  const session = await getSession();
  if (!session || !canApproveBookings(session.role)) return [];
  return getActiveTrackedVehicles();
}

/** Polled by the booking-details tracking card while a trip is running. */
export async function getTripTrackingStatusAction(tripId: string) {
  const session = await getSession();
  if (!session) return null;
  return getTripTrackingStatus(tripId);
}

export async function getTripLocationHistoryAction(tripId: string) {
  const session = await getSession();
  if (!session) return [];
  return getTripLocationHistory(tripId);
}
