import { tripsRepo, vehiclesRepo, driversRepo, bookingsRepo, vehicleLocationsRepo } from "@/lib/json-db/repositories";
import { nextId } from "@/lib/json-db/core";
import { AppError } from "@/lib/errors";
import type { VehicleLocationPing } from "@/lib/types";

export interface RecordLocationInput {
  tripId: string;
  lat: number;
  lng: number;
  actorUserId: string;
}

/** Feature #14: a driver's browser pings this while their trip is RUNNING.
 * Rejects pings from anyone but the trip's own assigned driver, and rejects
 * pings once the trip is no longer running (BR-style guard: tracking must
 * stop the moment a trip ends). Appends a history row and refreshes the
 * vehicle's "last known position" used by the admin live map. */
export async function recordVehicleLocation(input: RecordLocationInput): Promise<VehicleLocationPing> {
  const trip = await tripsRepo.findById(input.tripId);
  if (!trip) throw new AppError("ERR_NOT_FOUND", "Trip not found.");
  if (trip.status !== "RUNNING") {
    throw new AppError("ERR_BOOKING_NOT_EDITABLE", "This trip is no longer active — live tracking has stopped.");
  }

  const driver = trip.driverId ? await driversRepo.findById(trip.driverId) : undefined;
  if (!driver || driver.userId !== input.actorUserId) {
    throw new AppError("ERR_FORBIDDEN", "Only the assigned driver can share location for this trip.");
  }

  if (Number.isNaN(input.lat) || Number.isNaN(input.lng) || Math.abs(input.lat) > 90 || Math.abs(input.lng) > 180) {
    throw new AppError("ERR_VALIDATION", "Invalid coordinates.");
  }

  const id = await nextId("LOC");
  const now = new Date().toISOString();
  const ping: VehicleLocationPing = {
    id,
    tripId: trip.id,
    vehicleId: trip.vehicleId,
    driverId: trip.driverId,
    bookingId: trip.bookingId,
    lat: input.lat,
    lng: input.lng,
    recordedAt: now,
    createdAt: now,
    updatedAt: now,
  };
  await vehicleLocationsRepo.insert(ping);
  await vehiclesRepo.update(trip.vehicleId, { currentLat: input.lat, currentLng: input.lng, locationUpdatedAt: now });

  return ping;
}

export interface ActiveTrackedVehicle {
  vehicleId: string;
  vehicleName: string;
  registrationNumber: string;
  tripId: string;
  bookingId: string;
  driverId: string | null;
  driverName: string;
  lat: number;
  lng: number;
  updatedAt: string | null;
  tracking: boolean;
  pickupLocation: string;
  destinationLocation: string;
}

/** Feature #14 steps 5/8/9/10/15: everything the admin live fleet map needs —
 * one row per vehicle currently on a RUNNING trip, with its last known position. */
export async function getActiveTrackedVehicles(): Promise<ActiveTrackedVehicle[]> {
  const [runningTrips, vehicles, drivers, bookings] = await Promise.all([
    tripsRepo.findMany((t) => t.status === "RUNNING"),
    vehiclesRepo.findAll(),
    driversRepo.findAll(),
    bookingsRepo.findAll(),
  ]);

  const results: ActiveTrackedVehicle[] = [];
  for (const trip of runningTrips) {
    const vehicle = vehicles.find((v) => v.id === trip.vehicleId);
    if (!vehicle || vehicle.currentLat === undefined || vehicle.currentLng === undefined) continue;
    const driver = drivers.find((d) => d.id === trip.driverId);
    const booking = bookings.find((b) => b.id === trip.bookingId);

    results.push({
      vehicleId: vehicle.id,
      vehicleName: vehicle.vehicleName,
      registrationNumber: vehicle.registrationNumber,
      tripId: trip.id,
      bookingId: trip.bookingId,
      driverId: trip.driverId,
      driverName: driver?.driverName || "Unassigned",
      lat: vehicle.currentLat,
      lng: vehicle.currentLng,
      updatedAt: vehicle.locationUpdatedAt ?? null,
      tracking: true,
      pickupLocation: booking?.pickupLocation ?? "—",
      destinationLocation: booking?.destinationLocation ?? "—",
    });
  }
  return results;
}

export interface TrackingStatus {
  tracking: boolean;
  lat: number | null;
  lng: number | null;
  updatedAt: string | null;
}

/** Live status for a single trip — used by the booking-details tracking card,
 * polled every few seconds while the trip is running. */
export async function getTripTrackingStatus(tripId: string): Promise<TrackingStatus> {
  const trip = await tripsRepo.findById(tripId);
  if (!trip) throw new AppError("ERR_NOT_FOUND", "Trip not found.");
  const vehicle = await vehiclesRepo.findById(trip.vehicleId);

  return {
    tracking: trip.status === "RUNNING" && vehicle?.currentLat !== undefined,
    lat: vehicle?.currentLat ?? null,
    lng: vehicle?.currentLng ?? null,
    updatedAt: vehicle?.locationUpdatedAt ?? null,
  };
}

/** Feature #14 step 12/13: full breadcrumb trail for a trip, oldest first,
 * shown as a polyline once the trip has ended (or live, while running). */
export async function getTripLocationHistory(tripId: string) {
  const history = await vehicleLocationsRepo.findMany((p) => p.tripId === tripId);
  return history.sort((a, b) => a.recordedAt.localeCompare(b.recordedAt));
}
