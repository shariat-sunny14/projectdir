import { tripsRepo, bookingsRepo, vehiclesRepo, driversRepo, usersRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { writeAudit } from "@/lib/services/audit-service";
import { createNotification } from "@/lib/services/notification-service";
import { sendEmail } from "@/lib/services/email-service";
import { AppError } from "@/lib/errors";
import type { Trip } from "@/lib/types";

export interface StartTripInput {
  bookingId: string;
  startingKm?: number;
  startLocation?: string;
  startRemarks?: string;
  actorId: string;
}

/** BR-013/BR-014: trip can start only from an APPROVED booking; sets booking/vehicle/driver to ON_TRIP. */
export async function startTrip(input: StartTripInput): Promise<Trip> {
  const booking = await bookingsRepo.findById(input.bookingId);
  if (!booking) throw new AppError("ERR_NOT_FOUND", "Booking not found.");
  if (booking.status !== "APPROVED") {
    throw new AppError("ERR_BOOKING_NOT_EDITABLE", "Trip can only start from an approved booking.");
  }
  if (!booking.assignedVehicleId || !booking.assignedDriverId) {
    throw new AppError("ERR_VALIDATION", "Booking is missing a vehicle or driver assignment.");
  }

  const vehicle = await vehiclesRepo.findById(booking.assignedVehicleId);
  if (!vehicle) throw new AppError("ERR_NOT_FOUND", "Assigned vehicle not found.");

  const id = await nextId("TRP");
  const now = new Date().toISOString();
  const trip: Trip = {
    id,
    bookingId: booking.id,
    vehicleId: booking.assignedVehicleId,
    driverId: booking.assignedDriverId,
    actualStart: now,
    startingKm: input.startingKm ?? vehicle.currentKm,
    startLocation: input.startLocation || booking.pickupLocation,
    startRemarks: input.startRemarks,
    status: "RUNNING",
    createdAt: now,
    updatedAt: now,
  };
  await tripsRepo.insert(trip);

  await bookingsRepo.update(booking.id, { status: "ON_TRIP" });
  await vehiclesRepo.update(vehicle.id, { status: "ON_TRIP" });
  await driversRepo.update(booking.assignedDriverId, { status: "ON_TRIP" });

  await writeAudit(input.actorId, "Trip", "START_TRIP", id, `Booking ${booking.id}, starting KM ${trip.startingKm}`);

  return trip;
}

export interface CompleteTripInput {
  tripId: string;
  endingKm: number;
  endLocation?: string;
  endRemarks?: string;
  actorId: string;
}

/** BR-015/016/017/018: endKm >= startKm, totalKm = endKm - startKm, releases vehicle/driver,
 * updates vehicle.currentKm. */
export async function completeTrip(input: CompleteTripInput): Promise<Trip> {
  const trip = await tripsRepo.findById(input.tripId);
  if (!trip) throw new AppError("ERR_NOT_FOUND", "Trip not found.");
  if (trip.status !== "RUNNING") {
    throw new AppError("ERR_BOOKING_NOT_EDITABLE", "This trip has already been completed.");
  }
  if (input.endingKm < trip.startingKm) {
    throw new AppError("ERR_KM_INVALID", "Ending KM must be greater than or equal to starting KM.", "endingKm");
  }

  const now = new Date().toISOString();
  const totalKm = input.endingKm - trip.startingKm;

  const updatedTrip = await tripsRepo.update(trip.id, {
    actualEnd: now,
    endingKm: input.endingKm,
    endLocation: input.endLocation,
    endRemarks: input.endRemarks,
    totalKm,
    status: "COMPLETED",
  });
  if (!updatedTrip) throw new AppError("ERR_NOT_FOUND", "Trip not found.");

  await bookingsRepo.update(trip.bookingId, { status: "COMPLETED" });
  await vehiclesRepo.update(trip.vehicleId, { status: "AVAILABLE", currentKm: input.endingKm });
  if (trip.driverId) {
    await driversRepo.update(trip.driverId, { status: "AVAILABLE" });
  }

  await writeAudit(input.actorId, "Trip", "COMPLETE_TRIP", trip.id, `Total KM ${totalKm}`);

  const booking = await bookingsRepo.findById(trip.bookingId);
  if (booking) {
    const employee = await usersRepo.findById(booking.employeeId);
    if (employee) {
      await createNotification(
        employee.id,
        "Trip Completed",
        `Your trip for booking ${booking.id} has been completed. Total distance: ${totalKm} km.`,
        "TRIP_COMPLETED",
        booking.id
      );
      await sendEmail(
        employee.email,
        "TRIP_COMPLETED",
        `Trip completed for booking ${booking.id}`,
        `Hi ${employee.fullName}, your trip for booking ${booking.id} has been completed. Total distance: ${totalKm} km.`
      );
    }
  }

  return updatedTrip;
}

export async function getTripForBooking(bookingId: string) {
  const running = await tripsRepo.findOne((t) => t.bookingId === bookingId && t.status === "RUNNING");
  if (running) return running;
  return tripsRepo.findOne((t) => t.bookingId === bookingId);
}
