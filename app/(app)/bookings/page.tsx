import Link from "next/link";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canApproveBookings } from "@/lib/permissions";
import { bookingsRepo, usersRepo, vehiclesRepo, departmentsRepo, driversRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { Button } from "@/components/ui/button";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function BookingsPage({
  searchParams,
}: {
  searchParams: Promise<{ created?: string; from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  const params = await searchParams;

  const [allBookings, users, vehicles, departments, drivers] = await Promise.all([
    bookingsRepo.findAll(),
    usersRepo.findAll(),
    vehiclesRepo.findAll(),
    departmentsRepo.findAll(),
    driversRepo.findAll(),
  ]);

  const canApprove = canApproveBookings(session.role);
  const isDriver = session.role === "DRIVER";
  const myDriverRecord = isDriver ? drivers.find((d) => d.userId === session.userId) : undefined;

  let scoped = allBookings;
  let title = "All Bookings";
  let subtitle = "Review and manage vehicle booking requests.";

  if (canApprove) {
    // full list
  } else if (isDriver) {
    scoped = myDriverRecord ? allBookings.filter((b) => b.assignedDriverId === myDriverRecord.id) : [];
    title = "My Trips";
    subtitle = "Bookings assigned to you as driver.";
  } else {
    scoped = allBookings.filter((b) => b.employeeId === session.userId);
    title = "My Bookings";
    subtitle = "Track your vehicle booking requests.";
  }

  const filtered = filterByDateRange(scoped, "startDateTime", params.from, params.to).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const { items: bookings, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(params.page) || 1);

  const userName = (id: string) => users.find((u) => u.id === id)?.fullName || id;
  const deptName = (id?: string) => departments.find((d) => d.id === id)?.name || "—";
  const vehicleLabel = (id?: string | null) => (id ? vehicles.find((v) => v.id === id)?.registrationNumber || id : "—");

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>
        {!isDriver && (
          <Link href="/bookings/new">
            <Button>New Booking</Button>
          </Link>
        )}
      </div>

      {params.created && (
        <div className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
          Booking request submitted. It is now pending approval.
        </div>
      )}

      <DateRangeFilter dateLabel="Trip date" />

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Booking ID</th>
              {(canApprove || isDriver) && <th className="px-4 py-2">Employee</th>}
              <th className="px-4 py-2">Department</th>
              <th className="px-4 py-2">Start</th>
              <th className="px-4 py-2">End</th>
              <th className="px-4 py-2">Pickup → Destination</th>
              <th className="px-4 py-2">Requested</th>
              <th className="px-4 py-2">Assigned</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map((b) => (
              <tr key={b.id} className="border-b border-slate-50 last:border-0 align-top hover:bg-slate-50">
                <td className="px-4 py-2 font-medium text-indigo-600">
                  <Link href={`/bookings/${b.id}`} className="hover:underline">
                    {b.id}
                  </Link>
                </td>
                {(canApprove || isDriver) && <td className="px-4 py-2 text-slate-600">{userName(b.employeeId)}</td>}
                <td className="px-4 py-2 text-slate-500">{deptName(b.departmentId)}</td>
                <td className="px-4 py-2 text-slate-500">{new Date(b.startDateTime).toLocaleString()}</td>
                <td className="px-4 py-2 text-slate-500">{new Date(b.endDateTime).toLocaleString()}</td>
                <td className="px-4 py-2 text-slate-500">
                  {b.pickupLocation} → {b.destinationLocation}
                </td>
                <td className="px-4 py-2 text-slate-500">{vehicleLabel(b.requestedVehicleId)}</td>
                <td className="px-4 py-2 text-slate-500">{vehicleLabel(b.assignedVehicleId)}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={b.status} />
                </td>
              </tr>
            ))}
            {bookings.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-sm text-slate-400">
                  No bookings found for this range.
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <Pagination page={currentPage} totalPages={totalPages} totalItems={totalItems} />
      </div>
    </div>
  );
}
