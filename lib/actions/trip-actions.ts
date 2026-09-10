"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "@/lib/auth/session";
import { startTrip, completeTrip } from "@/lib/services/trip-service";
import { driversRepo, bookingsRepo, tripsRepo } from "@/lib/json-db/repositories";
import { canApproveBookings } from "@/lib/permissions";
import { AppError, runAction, type ActionResult } from "@/lib/errors";

/** Only an admin/manager, or the driver actually assigned to the booking, may
 * start or complete its trip. */
async function requireDriverOrManagerForBooking(bookingId: string) {
  const session = await getSession();
  if (!session) throw new AppError("ERR_FORBIDDEN", "Not authenticated.");
  if (canApproveBookings(session.role)) return session;

  if (session.role === "DRIVER") {
    const booking = await bookingsRepo.findById(bookingId);
    if (booking?.assignedDriverId) {
      const driver = await driversRepo.findById(booking.assignedDriverId);
      if (driver?.userId === session.userId) return session;
    }
  }
  throw new AppError("ERR_FORBIDDEN", "You are not assigned to this booking.");
}

async function requireDriverOrManagerForTrip(tripId: string) {
  const trip = await tripsRepo.findById(tripId);
  if (!trip) throw new AppError("ERR_NOT_FOUND", "Trip not found.");
  return requireDriverOrManagerForBooking(trip.bookingId);
}

export async function startTripAction(
  bookingId: string,
  startingKm: number | undefined,
  startLocation: string,
  startRemarks: string
): Promise<ActionResult<{ tripId: string }>> {
  return runAction(async () => {
    const session = await requireDriverOrManagerForBooking(bookingId);
    const trip = await startTrip({ bookingId, startingKm, startLocation, startRemarks, actorId: session.userId });
    revalidatePath("/bookings");
    revalidatePath(`/bookings/${bookingId}`);
    return { tripId: trip.id };
  });
}

export async function completeTripAction(
  tripId: string,
  bookingId: string,
  endingKm: number,
  endLocation: string,
  endRemarks: string
): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireDriverOrManagerForTrip(tripId);
    await completeTrip({ tripId, endingKm, endLocation, endRemarks, actorId: session.userId });
    revalidatePath("/bookings");
    revalidatePath(`/bookings/${bookingId}`);
    return null;
  });
}

/** Lets an admin manually toggle a driver's duty status from the drivers page. */
export async function setDriverDutyStatusAction(driverId: string, status: "AVAILABLE" | "OFF_DUTY") {
  await driversRepo.update(driverId, { status });
  revalidatePath("/admin/drivers");
}
