import { redirect, notFound } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { getSession } from "@/lib/auth/session";
import { canApproveBookings, isAdmin } from "@/lib/permissions";
import {
  bookingsRepo,
  usersRepo,
  vehiclesRepo,
  driversRepo,
  departmentsRepo,
  auditLogsRepo,
} from "@/lib/json-db/repositories";
import { getVehicleChangeHistory } from "@/lib/services/booking-service";
import { getTripForBooking } from "@/lib/services/trip-service";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApprovalPanel } from "./approval-panel";
import { ChangeVehiclePanel } from "./change-vehicle-panel";
import { TripPanel } from "./trip-panel";
import { CancelButton } from "./cancel-button";
import { RouteMapCard } from "./route-map-card";
import { VehicleTrackingCard } from "./vehicle-tracking-card";

export default async function BookingDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await getSession();
  if (!session) redirect("/login");

  const booking = await bookingsRepo.findById(id);
  if (!booking) notFound();

  const canApprove = canApproveBookings(session.role);
  const isOwner = booking.employeeId === session.userId;
  if (!canApprove && !isOwner && session.role !== "DRIVER") redirect("/bookings");

  const [employee, department, requestedVehicle, assignedVehicle, assignedDriver, vehicles, drivers, history, trip] =
    await Promise.all([
      usersRepo.findById(booking.employeeId),
      booking.departmentId ? departmentsRepo.findById(booking.departmentId) : undefined,
      vehiclesRepo.findById(booking.requestedVehicleId),
      booking.assignedVehicleId ? vehiclesRepo.findById(booking.assignedVehicleId) : undefined,
      booking.assignedDriverId ? driversRepo.findById(booking.assignedDriverId) : undefined,
      vehiclesRepo.findAll(),
      driversRepo.findAll(),
      getVehicleChangeHistory(booking.id),
      getTripForBooking(booking.id),
    ]);

  const allAudit = await auditLogsRepo.findAll();
  const relatedAudit = allAudit
    .filter((a) => a.recordId === booking.id || a.recordId === trip?.id)
    .sort((a, b) => b.createdAt.localeCompare(a.createdAt));

  const users = await usersRepo.findAll();
  const actorName = (userId: string) => users.find((u) => u.id === userId)?.fullName || userId;
  const vehicleName = (vehId: string | null) => (vehId ? vehicles.find((v) => v.id === vehId)?.vehicleName || vehId : "—");

  const isAssignedDriverUser = session.role === "DRIVER" && assignedDriver?.userId === session.userId;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link href="/bookings" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-600">
        <ArrowLeft size={16} /> Back to bookings
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{booking.id}</h1>
          <p className="text-sm text-slate-500">Created {new Date(booking.createdAt).toLocaleString()}</p>
        </div>
        <StatusBadge status={booking.status} />
      </div>

      {booking.status === "REJECTED" && booking.rejectionReason && (
        <div className="rounded-lg bg-rose-50 px-4 py-3 text-sm text-rose-700">
          <strong>Rejected:</strong> {booking.rejectionReason}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-3 font-semibold text-slate-900">Trip Information</h2>
          <dl className="space-y-2 text-sm">
            <Row label="Start" value={new Date(booking.startDateTime).toLocaleString()} />
            <Row label="End" value={new Date(booking.endDateTime).toLocaleString()} />
            <Row label="Pickup" value={booking.pickupLocation} />
            <Row label="Destination" value={booking.destinationLocation} />
            <Row label="Purpose" value={booking.purpose} />
            <Row label="Passenger Count" value={String(booking.passengerCount ?? "—")} />
            {booking.remarks && <Row label="Remarks" value={booking.remarks} />}
          </dl>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-3 font-semibold text-slate-900">Employee</h2>
          <dl className="space-y-2 text-sm">
            <Row label="Name" value={employee?.fullName || "—"} />
            <Row label="Department" value={department?.name || "—"} />
            <Row label="Phone" value={employee?.phone || "—"} />
            <Row label="Email" value={employee?.email || "—"} />
          </dl>
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-3 font-semibold text-slate-900">Vehicle</h2>
          <dl className="space-y-2 text-sm">
            <Row label="Requested Vehicle" value={requestedVehicle ? `${requestedVehicle.vehicleName} (${requestedVehicle.registrationNumber})` : "—"} />
            <Row
              label="Assigned Vehicle"
              value={assignedVehicle ? `${assignedVehicle.vehicleName} (${assignedVehicle.registrationNumber})` : "Not yet assigned"}
            />
          </dl>
          {canApprove && ["APPROVED", "ON_TRIP"].includes(booking.status) && (
            <div className="mt-3">
              <ChangeVehiclePanel bookingId={booking.id} currentVehicleId={booking.assignedVehicleId} vehicles={vehicles} />
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-3 font-semibold text-slate-900">Driver</h2>
          <dl className="space-y-2 text-sm">
            <Row label="Driver" value={assignedDriver?.driverName || "Not yet assigned"} />
            <Row label="Phone" value={assignedDriver?.phone || "—"} />
            <Row label="License" value={assignedDriver?.licenseNumber || "—"} />
          </dl>
        </section>
      </div>

      <RouteMapCard
        pickup={booking.pickupLocationDetails}
        destination={booking.destinationLocationDetails}
        pickupLabel={booking.pickupLocation}
        destinationLabel={booking.destinationLocation}
      />

      {canApprove && booking.status === "PENDING" && (
        <ApprovalPanel bookingId={booking.id} requestedVehicleId={booking.requestedVehicleId} vehicles={vehicles} drivers={drivers} />
      )}

      {(canApprove || isAssignedDriverUser) && (
        <TripPanel
          key={`${booking.status}-${trip?.id ?? "none"}-${assignedVehicle?.currentKm ?? "0"}`}
          booking={booking}
          trip={trip}
          isDriver={isAssignedDriverUser}
          vehicleCurrentKm={assignedVehicle?.currentKm}
        />
      )}

      {trip && (canApprove || isAssignedDriverUser || isOwner) && (
        <VehicleTrackingCard
          key={`${trip.id}-${trip.status}`}
          tripId={trip.id}
          isDriver={isAssignedDriverUser}
          tripStatus={trip.status}
          vehicleName={assignedVehicle?.vehicleName}
        />
      )}

      {isOwner && booking.status === "PENDING" && (
        <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-2 font-semibold text-slate-900">Cancel Booking</h2>
          <p className="mb-3 text-sm text-slate-500">You can cancel this booking while it&apos;s still pending approval.</p>
          <CancelButton bookingId={booking.id} />
        </div>
      )}

      {isAdmin(session.role) && booking.status === "APPROVED" && (
        <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-2 font-semibold text-slate-900">Cancel Booking</h2>
          <p className="mb-3 text-sm text-slate-500">
            This booking is already approved — only Super Admin / Admin can cancel it from here on.
          </p>
          <CancelButton bookingId={booking.id} />
        </div>
      )}

      {history.length > 0 && (
        <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-3 font-semibold text-slate-900">Vehicle Change History</h2>
          <ul className="space-y-2 text-sm">
            {history.map((h) => (
              <li key={h.id} className="border-b border-slate-50 pb-2 last:border-0">
                <p className="text-slate-700">
                  {vehicleName(h.oldVehicleId)} → {vehicleName(h.newVehicleId)}
                </p>
                <p className="text-xs text-slate-400">
                  {actorName(h.changedBy)} · {new Date(h.changedAt).toLocaleString()} · {h.reason}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}

      {canApprove && relatedAudit.length > 0 && (
        <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
          <h2 className="mb-3 font-semibold text-slate-900">Audit Activity</h2>
          <ul className="space-y-2 text-sm">
            {relatedAudit.map((a) => (
              <li key={a.id} className="border-b border-slate-50 pb-2 last:border-0">
                <p className="text-slate-700">
                  {a.action.replaceAll("_", " ")} — {actorName(a.userId)}
                </p>
                {a.description && <p className="text-xs text-slate-400">{a.description}</p>}
                <p className="text-xs text-slate-300">{new Date(a.createdAt).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-400">{label}</dt>
      <dd className="text-right font-medium text-slate-700">{value}</dd>
    </div>
  );
}
