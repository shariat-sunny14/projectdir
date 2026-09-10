"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "@/lib/auth/session";
import { canApproveBookings } from "@/lib/permissions";
import {
  createBooking,
  approveBooking,
  rejectBooking,
  cancelBooking,
  changeBookingVehicle,
} from "@/lib/services/booking-service";
import { usersRepo } from "@/lib/json-db/repositories";
import { AppError, runAction, type ActionResult } from "@/lib/errors";
import { parseGeoLocationField } from "@/lib/validators/location";

export async function createBookingAction(formData: FormData): Promise<ActionResult<{ id: string }>> {
  return runAction(async () => {
    const session = await getSession();
    if (!session) throw new AppError("ERR_FORBIDDEN", "Not authenticated.");

    const user = await usersRepo.findById(session.userId);

    const startDate = String(formData.get("startDate"));
    const startTime = String(formData.get("startTime"));
    const endDate = String(formData.get("endDate"));
    const endTime = String(formData.get("endTime"));

    const pickupLocationDetails = parseGeoLocationField(formData.get("pickupLocationDetails"));
    const destinationLocationDetails = parseGeoLocationField(formData.get("destinationLocationDetails"));
    if (!pickupLocationDetails || !destinationLocationDetails) {
      throw new AppError("ERR_VALIDATION", "Select a pickup and a destination location from the suggestions.");
    }

    const booking = await createBooking({
      employeeId: session.userId,
      departmentId: user?.departmentId,
      startDateTime: `${startDate}T${startTime}:00`,
      endDateTime: `${endDate}T${endTime}:00`,
      pickupLocation: pickupLocationDetails.name,
      destinationLocation: destinationLocationDetails.name,
      pickupLocationDetails,
      destinationLocationDetails,
      purpose: String(formData.get("purpose")),
      passengerCount: formData.get("passengerCount") ? Number(formData.get("passengerCount")) : undefined,
      remarks: String(formData.get("remarks") || ""),
      requestedVehicleId: String(formData.get("requestedVehicleId")),
    });

    return { id: booking.id };
  });
}

async function requireApprover() {
  const session = await getSession();
  if (!session || !canApproveBookings(session.role)) {
    throw new AppError("ERR_FORBIDDEN", "Not authorized.");
  }
  return session;
}

export async function approveBookingAction(bookingId: string, vehicleId: string, driverId: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireApprover();
    await approveBooking(bookingId, vehicleId, driverId, session.userId);
    revalidatePath("/bookings");
    revalidatePath(`/bookings/${bookingId}`);
    return null;
  });
}

export async function rejectBookingAction(bookingId: string, reason: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireApprover();
    await rejectBooking(bookingId, session.userId, reason || "Not specified");
    revalidatePath("/bookings");
    revalidatePath(`/bookings/${bookingId}`);
    return null;
  });
}

export async function cancelBookingAction(bookingId: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await getSession();
    if (!session) throw new AppError("ERR_FORBIDDEN", "Not authenticated.");
    await cancelBooking(bookingId, session.userId, session.role);
    revalidatePath("/bookings");
    revalidatePath(`/bookings/${bookingId}`);
    return null;
  });
}

export async function changeBookingVehicleAction(bookingId: string, newVehicleId: string, reason: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await requireApprover();
    await changeBookingVehicle(bookingId, newVehicleId, reason, session.userId);
    revalidatePath("/bookings");
    revalidatePath(`/bookings/${bookingId}`);
    return null;
  });
}
