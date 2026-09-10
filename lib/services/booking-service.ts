import { bookingsRepo, vehiclesRepo, driversRepo, usersRepo, bookingVehicleHistoryRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { writeAudit } from "@/lib/services/audit-service";
import { sendEmail } from "@/lib/services/email-service";
import { createNotification } from "@/lib/services/notification-service";
import { isVehicleAvailable, isDriverAvailable } from "@/lib/services/availability-service";
import { AppError } from "@/lib/errors";
import type { Booking, GeoLocation } from "@/lib/types";

// Re-export so existing callers (booking wizard API route) keep working.
export { getAvailableVehicles, getAvailableDrivers } from "@/lib/services/availability-service";

export interface CreateBookingInput {
  employeeId: string;
  departmentId?: string;
  startDateTime: string;
  endDateTime: string;
  pickupLocation: string;
  destinationLocation: string;
  pickupLocationDetails?: GeoLocation;
  destinationLocationDetails?: GeoLocation;
  purpose: string;
  passengerCount?: number;
  remarks?: string;
  requestedVehicleId: string;
}

export async function createBooking(input: CreateBookingInput): Promise<Booking> {
  if (new Date(input.startDateTime) >= new Date(input.endDateTime)) {
    throw new AppError("ERR_INVALID_RANGE", "End time must be after start time.", "endDateTime");
  }

  const vehicle = await vehiclesRepo.findById(input.requestedVehicleId);
  if (!vehicle) throw new AppError("ERR_NOT_FOUND", "Selected vehicle was not found.", "requestedVehicleId");

  // Phase 10: re-check conflict server-side even though the wizard already filtered by availability.
  const available = await isVehicleAvailable(vehicle, input.startDateTime, input.endDateTime);
  if (!available) {
    throw new AppError("ERR_VEHICLE_CONFLICT", "This vehicle is already booked for the selected time.", "requestedVehicleId");
  }

  const id = await nextId("BK");
  const now = new Date().toISOString();
  const booking: Booking = {
    id,
    employeeId: input.employeeId,
    departmentId: input.departmentId,
    startDateTime: input.startDateTime,
    endDateTime: input.endDateTime,
    pickupLocation: input.pickupLocation,
    destinationLocation: input.destinationLocation,
    pickupLocationDetails: input.pickupLocationDetails,
    destinationLocationDetails: input.destinationLocationDetails,
    purpose: input.purpose,
    passengerCount: input.passengerCount,
    remarks: input.remarks,
    requestedVehicleId: input.requestedVehicleId,
    assignedVehicleId: null,
    assignedDriverId: null,
    status: "PENDING",
    createdAt: now,
    updatedAt: now,
  };
  await bookingsRepo.insert(booking);
  await writeAudit(input.employeeId, "Booking", "CREATE", id, `Requested vehicle ${input.requestedVehicleId}`);

  const managers = (await usersRepo.findAll()).filter((u) => ["SUPER_ADMIN", "ADMIN", "TRANSPORT_MANAGER"].includes(u.role));
  await Promise.all(
    managers.map((m) => createNotification(m.id, "New Booking Request", `Booking ${id} is awaiting your review.`, "BOOKING_CREATED", id))
  );

  return booking;
}

/** Phase 12: approval requires both a vehicle and a driver, re-checks both for
 * conflicts server-side, then applies all side effects. */
export async function approveBooking(bookingId: string, vehicleId: string, driverId: string, actorId: string): Promise<Booking> {
  const booking = await bookingsRepo.findById(bookingId);
  if (!booking) throw new AppError("ERR_NOT_FOUND", "Booking not found.");
  if (booking.status !== "PENDING") {
    throw new AppError("ERR_BOOKING_NOT_EDITABLE", "Only a pending booking can be approved.");
  }
  if (!vehicleId) throw new AppError("ERR_VALIDATION", "A vehicle must be selected.", "vehicleId");
  if (!driverId) throw new AppError("ERR_VALIDATION", "A driver must be selected.", "driverId");

  const vehicle = await vehiclesRepo.findById(vehicleId);
  if (!vehicle) throw new AppError("ERR_NOT_FOUND", "Vehicle not found.", "vehicleId");
  const driver = await driversRepo.findById(driverId);
  if (!driver) throw new AppError("ERR_NOT_FOUND", "Driver not found.", "driverId");

  const vehicleOk = await isVehicleAvailable(vehicle, booking.startDateTime, booking.endDateTime, booking.id);
  if (!vehicleOk) {
    throw new AppError("ERR_VEHICLE_CONFLICT", "This vehicle is already booked for the selected time.", "vehicleId");
  }
  const driverOk = await isDriverAvailable(driver, booking.startDateTime, booking.endDateTime, booking.id);
  if (!driverOk) {
    throw new AppError("ERR_DRIVER_CONFLICT", "This driver is already assigned for the selected time.", "driverId");
  }

  const updated = await bookingsRepo.update(bookingId, {
    status: "APPROVED",
    assignedVehicleId: vehicleId,
    assignedDriverId: driverId,
  });
  if (!updated) throw new AppError("ERR_NOT_FOUND", "Booking not found.");

  await vehiclesRepo.update(vehicleId, { status: "BOOKED" });
  await driversRepo.update(driverId, { status: "BOOKED" });

  await writeAudit(actorId, "Booking", "APPROVE", bookingId, `Vehicle ${vehicleId}, Driver ${driverId}`);

  const employee = await usersRepo.findById(booking.employeeId);
  if (employee) {
    await createNotification(
      employee.id,
      "Booking Approved",
      `Your booking ${bookingId} has been approved. Vehicle: ${vehicle.registrationNumber}, Driver: ${driver.driverName}.`,
      "BOOKING_APPROVED",
      bookingId
    );
    await sendEmail(
      employee.email,
      "BOOKING_APPROVED",
      `Booking ${bookingId} approved`,
      `Hi ${employee.fullName}, your booking ${bookingId} (${booking.pickupLocation} to ${booking.destinationLocation}) has been approved. Vehicle: ${vehicle.registrationNumber}. Driver: ${driver.driverName}.`
    );
  }

  return updated;
}

/** Phase 12: rejected booking releases any reservation and cannot hold a vehicle/driver. */
export async function rejectBooking(bookingId: string, actorId: string, reason: string): Promise<Booking> {
  const booking = await bookingsRepo.findById(bookingId);
  if (!booking) throw new AppError("ERR_NOT_FOUND", "Booking not found.");
  if (booking.status !== "PENDING") {
    throw new AppError("ERR_BOOKING_NOT_EDITABLE", "Only a pending booking can be rejected.");
  }

  const updated = await bookingsRepo.update(bookingId, {
    status: "REJECTED",
    rejectionReason: reason,
    assignedVehicleId: null,
    assignedDriverId: null,
  });
  if (!updated) throw new AppError("ERR_NOT_FOUND", "Booking not found.");

  await writeAudit(actorId, "Booking", "REJECT", bookingId, reason);

  const employee = await usersRepo.findById(booking.employeeId);
  if (employee) {
    await createNotification(employee.id, "Booking Rejected", `Your booking ${bookingId} was rejected. Reason: ${reason}`, "BOOKING_REJECTED", bookingId);
    await sendEmail(
      employee.email,
      "BOOKING_REJECTED",
      `Booking ${bookingId} rejected`,
      `Hi ${employee.fullName}, your booking ${bookingId} was rejected.\nReason: ${reason}`
    );
  }

  return updated;
}

/** Employee-initiated cancellation. BR-019 / BR-021: can't cancel a started trip;
 * cancelling releases any vehicle/driver reservation. Once a booking is APPROVED,
 * only an admin can cancel it (the employee can no longer self-cancel). */
export async function cancelBooking(bookingId: string, actorId: string, actorRole: string): Promise<Booking> {
  const booking = await bookingsRepo.findById(bookingId);
  if (!booking) throw new AppError("ERR_NOT_FOUND", "Booking not found.");
  if (!["PENDING", "APPROVED"].includes(booking.status)) {
    throw new AppError("ERR_BOOKING_NOT_CANCELABLE", "This booking can no longer be cancelled.");
  }

  const isAdminActor = ["SUPER_ADMIN", "ADMIN"].includes(actorRole);
  if (booking.status === "APPROVED" && !isAdminActor) {
    throw new AppError("ERR_FORBIDDEN", "This booking is already approved — only Super Admin / Admin can cancel it now.");
  }

  const updated = await bookingsRepo.update(bookingId, { status: "CANCELLED" });
  if (!updated) throw new AppError("ERR_NOT_FOUND", "Booking not found.");

  if (booking.assignedVehicleId) {
    await vehiclesRepo.update(booking.assignedVehicleId, { status: "AVAILABLE" });
  }
  if (booking.assignedDriverId) {
    await driversRepo.update(booking.assignedDriverId, { status: "AVAILABLE" });
  }

  await writeAudit(actorId, "Booking", "CANCEL", bookingId);

  const employee = await usersRepo.findById(booking.employeeId);
  const actor = await usersRepo.findById(actorId);
  if (employee) {
    await createNotification(
      employee.id,
      "Booking Cancelled",
      `Booking ${bookingId} (${booking.pickupLocation} to ${booking.destinationLocation}) has been cancelled.`,
      "SYSTEM",
      bookingId
    );
    await sendEmail(
      employee.email,
      "BOOKING_CANCELLED",
      `Booking ${bookingId} cancelled`,
      `Hi ${employee.fullName}, booking ${bookingId} (${booking.pickupLocation} to ${booking.destinationLocation}, ${booking.startDateTime} to ${booking.endDateTime}) has been cancelled${actor && actor.id !== employee.id ? ` by ${actor.fullName}` : ""}.`
    );
  }

  // Also let managers know a slot just freed up, if an admin/manager did the cancelling on someone else's behalf.
  if (actor && actor.id !== booking.employeeId) {
    const managers = (await usersRepo.findAll()).filter((u) => ["SUPER_ADMIN", "ADMIN", "TRANSPORT_MANAGER"].includes(u.role) && u.id !== actor.id);
    await Promise.all(
      managers.map((m) => createNotification(m.id, "Booking Cancelled", `Booking ${bookingId} was cancelled.`, "SYSTEM", bookingId))
    );
  }

  return updated;
}

/** Phase 13/14/15: change the final assigned vehicle. requestedVehicleId never changes. */
export async function changeBookingVehicle(bookingId: string, newVehicleId: string, reason: string, actorId: string): Promise<Booking> {
  const booking = await bookingsRepo.findById(bookingId);
  if (!booking) throw new AppError("ERR_NOT_FOUND", "Booking not found.");
  if (!["APPROVED", "ON_TRIP"].includes(booking.status)) {
    throw new AppError("ERR_BOOKING_NOT_EDITABLE", "Vehicle can only be changed on an approved booking.");
  }
  if (!reason) throw new AppError("ERR_VALIDATION", "A change reason is required.", "reason");

  const newVehicle = await vehiclesRepo.findById(newVehicleId);
  if (!newVehicle) throw new AppError("ERR_NOT_FOUND", "Vehicle not found.", "newVehicleId");

  const available = await isVehicleAvailable(newVehicle, booking.startDateTime, booking.endDateTime, booking.id);
  if (!available) {
    throw new AppError("ERR_VEHICLE_CONFLICT", "This vehicle is already booked for the selected time.", "newVehicleId");
  }

  const oldVehicleId = booking.assignedVehicleId;
  const updated = await bookingsRepo.update(bookingId, { assignedVehicleId: newVehicleId });
  if (!updated) throw new AppError("ERR_NOT_FOUND", "Booking not found.");

  if (oldVehicleId) await vehiclesRepo.update(oldVehicleId, { status: "AVAILABLE" });
  await vehiclesRepo.update(newVehicleId, { status: booking.status === "ON_TRIP" ? "ON_TRIP" : "BOOKED" });

  const historyId = await nextId("VCH");
  const now = new Date().toISOString();
  await bookingVehicleHistoryRepo.insert({
    id: historyId,
    bookingId,
    oldVehicleId,
    newVehicleId,
    changedBy: actorId,
    reason,
    changedAt: now,
    createdAt: now,
    updatedAt: now,
  });

  await writeAudit(actorId, "Booking", "VEHICLE_CHANGE", bookingId, `${oldVehicleId ?? "none"} -> ${newVehicleId}: ${reason}`);

  const employee = await usersRepo.findById(booking.employeeId);
  const oldVehicle = oldVehicleId ? await vehiclesRepo.findById(oldVehicleId) : undefined;
  if (employee) {
    await createNotification(
      employee.id,
      "Vehicle Changed",
      `Your vehicle for booking ${bookingId} has been changed from ${oldVehicle?.vehicleName ?? "—"} to ${newVehicle.vehicleName}.`,
      "VEHICLE_CHANGED",
      bookingId
    );
    await sendEmail(
      employee.email,
      "VEHICLE_CHANGED",
      `Vehicle changed for booking ${bookingId}`,
      `Hi ${employee.fullName},\n\nYour vehicle for booking ${bookingId} has changed.\nRequested: ${oldVehicle?.vehicleName ?? "—"}\nAssigned: ${newVehicle.vehicleName}\nWhen: ${booking.startDateTime} to ${booking.endDateTime}\nPickup: ${booking.pickupLocation}\nDestination: ${booking.destinationLocation}\nReason: ${reason}`
    );
  }

  return updated;
}

export async function getVehicleChangeHistory(bookingId: string) {
  const history = await bookingVehicleHistoryRepo.findMany((h) => h.bookingId === bookingId);
  return history.sort((a, b) => b.changedAt.localeCompare(a.changedAt));
}
