import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData } from "@/lib/permissions";
import { driversRepo, vehiclesRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { DriverForm } from "./driver-form";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function DriversPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!canManageMasterData(session.role)) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const [allDrivers, vehicles] = await Promise.all([driversRepo.findAll(), vehiclesRepo.findAll()]);
  const vehicleLabel = (id?: string) => vehicles.find((v) => v.id === id)?.registrationNumber || "—";

  const filtered = filterByDateRange(allDrivers, "createdAt", from, to).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const { items: drivers, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(page) || 1);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Drivers</h1>
          <p className="text-sm text-slate-500">Operational driver roster.</p>
        </div>
        <DriverForm mode="create" vehicles={vehicles} />
      </div>

      <DateRangeFilter dateLabel="Joined" />

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Driver ID</th>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Phone</th>
              <th className="px-4 py-2">License</th>
              <th className="px-4 py-2">License Expiry</th>
              <th className="px-4 py-2">Assigned Vehicle</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {drivers.map((d) => (
              <tr key={d.id} className="border-b border-slate-50 last:border-0">
                <td className="px-4 py-2 font-medium text-slate-700">{d.id}</td>
                <td className="px-4 py-2 text-slate-700">{d.driverName}</td>
                <td className="px-4 py-2 text-slate-500">{d.phone}</td>
                <td className="px-4 py-2 text-slate-500">{d.licenseNumber}</td>
                <td className="px-4 py-2 text-slate-500">{d.licenseExpiryDate}</td>
                <td className="px-4 py-2 text-slate-500">{vehicleLabel(d.assignedVehicleId)}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={d.status} />
                </td>
                <td className="px-4 py-2">
                  <DriverForm mode="edit" driver={d} vehicles={vehicles} />
                </td>
              </tr>
            ))}
            {drivers.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-6 text-center text-sm text-slate-400">
                  No drivers found for this range.
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
