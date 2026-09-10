import { Car, CheckCircle2, Clock, Users, Wrench, UserCheck, Gauge, Navigation, Radar } from "lucide-react";
import Link from "next/link";
import { getSession } from "@/lib/auth/session";
import { redirect } from "next/navigation";
import { vehiclesRepo, driversRepo, bookingsRepo, usersRepo, expensesRepo } from "@/lib/json-db/repositories";
import { StatCard } from "@/components/dashboard/stat-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { isAdmin } from "@/lib/permissions";
import { filterByDateRange, bucketTimeSeries } from "@/lib/utils/list-helpers";
import { BookingsTrendChart, VehicleStatusChart, ExpenseByCategoryChart } from "@/components/dashboard/charts";
import type { ExpenseCategory } from "@/lib/types";

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");

  const [vehicles, drivers, bookings, users] = await Promise.all([
    vehiclesRepo.findAll(),
    driversRepo.findAll(),
    bookingsRepo.findAll(),
    usersRepo.findAll(),
  ]);

  if (session.role === "DRIVER") {
    const myDriverRecord = drivers.find((d) => d.userId === session.userId);
    const myTrips = bookings.filter((b) => b.assignedDriverId === myDriverRecord?.id);
    const activeTrip = myTrips.find((b) => b.status === "ON_TRIP");
    const activeVehicle = activeTrip ? vehicles.find((v) => v.id === activeTrip.assignedVehicleId) : undefined;

    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Driver Dashboard</h1>

        {activeTrip ? (
          <Link
            href={`/bookings/${activeTrip.id}`}
            className="flex items-center justify-between gap-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 p-5 text-white shadow-lg shadow-blue-600/30 transition-transform hover:scale-[1.01]"
          >
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/15">
                <Navigation size={22} className="animate-pulse" />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-blue-100">You are currently ON TRIP</p>
                <p className="text-lg font-semibold">
                  {activeTrip.id} · {activeVehicle?.vehicleName ?? "Vehicle"}
                </p>
                <p className="text-sm text-blue-100">
                  {activeTrip.pickupLocation} → {activeTrip.destinationLocation}
                </p>
              </div>
            </div>
            <span className="hidden shrink-0 rounded-lg bg-white/15 px-3 py-1.5 text-sm font-medium sm:block">Complete Trip →</span>
          </Link>
        ) : (
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 text-sm text-slate-500 shadow-sm shadow-slate-200/50">
            You have no trip in progress right now.
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Assigned Trips" value={myTrips.filter((b) => b.status === "APPROVED").length} icon={Clock} tone="amber" />
          <StatCard label="On Trip" value={myTrips.filter((b) => b.status === "ON_TRIP").length} icon={Navigation} tone="blue" />
          <StatCard label="Completed Trips" value={myTrips.filter((b) => b.status === "COMPLETED").length} icon={CheckCircle2} tone="emerald" />
          <StatCard label="Assigned Vehicle" value={vehicles.find((v) => v.id === myDriverRecord?.assignedVehicleId)?.registrationNumber ?? "—"} icon={Car} />
        </div>
      </div>
    );
  }

  if (session.role === "EMPLOYEE") {
    const mine = bookings.filter((b) => b.employeeId === session.userId);
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">My Dashboard</h1>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Available Vehicles" value={vehicles.filter((v) => v.status === "AVAILABLE").length} icon={Car} tone="emerald" />
          <StatCard label="My Pending Bookings" value={mine.filter((b) => b.status === "PENDING").length} icon={Clock} tone="amber" />
          <StatCard label="My Upcoming Bookings" value={mine.filter((b) => b.status === "APPROVED").length} icon={CheckCircle2} tone="blue" />
          <StatCard label="Completed Trips" value={mine.filter((b) => b.status === "COMPLETED").length} icon={CheckCircle2} tone="emerald" />
        </div>
      </div>
    );
  }

  // Admin / Transport Manager dashboard
  const { from: fromParam, to: toParam } = await searchParams;
  const today = new Date().toISOString().slice(0, 10);
  const from = fromParam || today; // default range: today only, matching the "Today" preset
  const to = toParam || today;

  const todaysBookings = bookings.filter((b) => b.startDateTime.slice(0, 10) === today);
  const expenses = await expensesRepo.findAll();

  const rangeBookings = filterByDateRange(bookings, "startDateTime", from, to);
  const rangeExpenses = filterByDateRange(expenses, "expenseDate", from, to).filter((e) => e.approvalStatus === "APPROVED");

  const bookingsTrend = bucketTimeSeries(
    rangeBookings.map((b) => b.startDateTime),
    from,
    to
  );

  const vehicleStatusData = ["AVAILABLE", "BOOKED", "ON_TRIP", "MAINTENANCE", "INACTIVE"].map((status) => ({
    name: status,
    value: vehicles.filter((v) => v.status === status).length,
  }));

  const categories: ExpenseCategory[] = ["FUEL", "TOLL", "TIP", "PARKING", "REPAIR", "SERVICE", "INSURANCE", "TAX", "OTHER"];
  const expenseByCategory = categories.map((c) => ({
    category: c,
    amount: rangeExpenses.filter((e) => e.category === c).reduce((s, e) => s + e.amount, 0),
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Admin Dashboard</h1>
        <DateRangeFilter dateLabel="Range" />
      </div>

      <Link
        href="/admin/live-tracking"
        className="flex items-center justify-between gap-4 rounded-2xl bg-gradient-to-r from-slate-900 to-indigo-950 p-5 text-white shadow-lg shadow-slate-900/20 transition-transform hover:scale-[1.01]"
      >
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/10">
            <Radar size={22} className="animate-pulse text-emerald-400" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-indigo-200">Live Fleet Tracking</p>
            <p className="text-lg font-semibold">{vehicles.filter((v) => v.status === "ON_TRIP").length} vehicle(s) on the road right now</p>
            <p className="text-sm text-indigo-200">See real-time position, driver and booking for every active trip.</p>
          </div>
        </div>
        <span className="hidden shrink-0 rounded-lg bg-white/10 px-3 py-1.5 text-sm font-medium sm:block">Open Live Map →</span>
      </Link>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Vehicles" value={vehicles.length} icon={Car} />
        <StatCard label="Available Vehicles" value={vehicles.filter((v) => v.status === "AVAILABLE").length} icon={CheckCircle2} tone="emerald" />
        <StatCard label="Approved Vehicles" value={vehicles.filter((v) => v.status === "BOOKED").length} icon={CheckCircle2} tone="amber" />
        <StatCard label="On Trip" value={vehicles.filter((v) => v.status === "ON_TRIP").length} icon={Gauge} tone="blue" />
        <StatCard label="Maintenance" value={vehicles.filter((v) => v.status === "MAINTENANCE").length} icon={Wrench} tone="amber" />
        <StatCard label="Total Drivers" value={drivers.length} icon={Users} />
        <StatCard label="Today's Bookings" value={todaysBookings.length} icon={Clock} tone="blue" />
        {isAdmin(session.role) && (
          <StatCard label="Pending User Approvals" value={users.filter((u) => u.status === "PENDING").length} icon={UserCheck} tone="amber" />
        )}
        <StatCard label="Pending Booking Approvals" value={bookings.filter((b) => b.status === "PENDING").length} icon={Clock} tone="rose" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <BookingsTrendChart data={bookingsTrend} />
        </div>
        <VehicleStatusChart data={vehicleStatusData} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
            <div className="border-b border-slate-200 px-4 py-3">
              <h2 className="font-semibold text-slate-900">Today&apos;s Trips</h2>
            </div>
            {todaysBookings.length === 0 ? (
              <p className="px-4 py-6 text-sm text-slate-400">No trips scheduled for today.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      <th className="px-4 py-2">Booking ID</th>
                      <th className="px-4 py-2">Pickup</th>
                      <th className="px-4 py-2">Destination</th>
                      <th className="px-4 py-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {todaysBookings.map((b) => (
                      <tr key={b.id} className="border-b border-slate-50 last:border-0">
                        <td className="px-4 py-2 font-medium text-slate-700">{b.id}</td>
                        <td className="px-4 py-2 text-slate-600">{b.pickupLocation}</td>
                        <td className="px-4 py-2 text-slate-600">{b.destinationLocation}</td>
                        <td className="px-4 py-2">
                          <StatusBadge status={b.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
        <ExpenseByCategoryChart data={expenseByCategory} />
      </div>
    </div>
  );
}
