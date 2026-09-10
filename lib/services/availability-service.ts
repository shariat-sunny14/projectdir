import { bookingsRepo, vehiclesRepo, driversRepo, maintenanceRepo } from "@/lib/json-db/repositories";
import { BLOCKING_BOOKING_STATUSES } from "@/lib/types";
import type { Vehicle, Driver, Booking } from "@/lib/types";

/** BR-006 / BR-007: startA < endB AND startB < endA. Used identically for
 * vehicle availability, driver availability, and reassignment checks. */
export function overlaps(aStart: string, aEnd: string, bStart: string, bEnd: string): boolean {
  return new Date(aStart) < new Date(bEnd) && new Date(bStart) < new Date(aEnd);
}

function isBlockingBooking(b: Booking): boolean {
  return (BLOCKING_BOOKING_STATUSES as readonly string[]).includes(b.status);
}

/** Bookings for a vehicle that would block a new/changed reservation in the given window,
 * optionally excluding one booking (e.g. the booking currently being approved/changed). */
export async function getBlockingBookingsForVehicle(
  vehicleId: string,
  startDateTime: string,
  endDateTime: string,
  excludeBookingId?: string
): Promise<Booking[]> {
  const bookings = await bookingsRepo.findAll();
  return bookings.filter(
    (b) =>
      b.id !== excludeBookingId &&
      isBlockingBooking(b) &&
      (b.assignedVehicleId === vehicleId || (!b.assignedVehicleId && b.requestedVehicleId === vehicleId)) &&
      overlaps(b.startDateTime, b.endDateTime, startDateTime, endDateTime)
  );
}

export async function getBlockingBookingsForDriver(
  driverId: string,
  startDateTime: string,
  endDateTime: string,
  excludeBookingId?: string
): Promise<Booking[]> {
  const bookings = await bookingsRepo.findAll();
  return bookings.filter(
    (b) =>
      b.id !== excludeBookingId &&
      isBlockingBooking(b) &&
      b.assignedDriverId === driverId &&
      overlaps(b.startDateTime, b.endDateTime, startDateTime, endDateTime)
  );
}

async function hasOpenMaintenance(vehicleId: string): Promise<boolean> {
  const records = await maintenanceRepo.findMany((m) => m.vehicleId === vehicleId && m.status === "OPEN");
  return records.length > 0;
}

/** Phase 09 / BR-004 / BR-005: a vehicle is unavailable when MAINTENANCE, INACTIVE,
 * it has an open service record, or a blocking booking overlaps the window. */
export async function isVehicleAvailable(
  vehicle: Vehicle,
  startDateTime: string,
  endDateTime: string,
  excludeBookingId?: string
): Promise<boolean> {
  if (vehicle.status === "MAINTENANCE" || vehicle.status === "INACTIVE") return false;
  if (await hasOpenMaintenance(vehicle.id)) return false;
  const blocking = await getBlockingBookingsForVehicle(vehicle.id, startDateTime, endDateTime, excludeBookingId);
  return blocking.length === 0;
}

export async function isDriverAvailable(
  driver: Driver,
  startDateTime: string,
  endDateTime: string,
  excludeBookingId?: string
): Promise<boolean> {
  if (driver.status === "OFF_DUTY" || driver.status === "INACTIVE") return false;
  const blocking = await getBlockingBookingsForDriver(driver.id, startDateTime, endDateTime, excludeBookingId);
  return blocking.length === 0;
}

export async function getAvailableVehicles(
  startDateTime: string,
  endDateTime: string,
  excludeBookingId?: string
): Promise<Vehicle[]> {
  const vehicles = await vehiclesRepo.findAll();
  const results: Vehicle[] = [];
  for (const v of vehicles) {
    if (await isVehicleAvailable(v, startDateTime, endDateTime, excludeBookingId)) results.push(v);
  }
  return results;
}

export async function getAvailableDrivers(
  startDateTime: string,
  endDateTime: string,
  excludeBookingId?: string
): Promise<Driver[]> {
  const drivers = await driversRepo.findAll();
  const results: Driver[] = [];
  for (const d of drivers) {
    if (await isDriverAvailable(d, startDateTime, endDateTime, excludeBookingId)) results.push(d);
  }
  return results;
}
