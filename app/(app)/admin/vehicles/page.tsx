import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData } from "@/lib/permissions";
import { vehiclesRepo, departmentsRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { VehicleForm } from "./vehicle-form";
import { AlertTriangle } from "lucide-react";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

function isExpiringOrExpired(dateStr?: string) {
  if (!dateStr) return false;
  const d = new Date(dateStr);
  const in30 = new Date();
  in30.setDate(in30.getDate() + 30);
  return d < in30;
}

export default async function VehiclesPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!canManageMasterData(session.role)) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const [allVehicles, departments] = await Promise.all([vehiclesRepo.findAll(), departmentsRepo.findAll()]);
  const deptName = (id?: string) => departments.find((d) => d.id === id)?.name || "—";

  const filtered = filterByDateRange(allVehicles, "createdAt", from, to).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const { items: vehicles, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(page) || 1);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Vehicles</h1>
          <p className="text-sm text-slate-500">Fleet inventory and document tracking.</p>
        </div>
        <VehicleForm mode="create" departments={departments} />
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <DateRangeFilter dateLabel="Added" />
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Reg. No.</th>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Fuel</th>
              <th className="px-4 py-2">Dept.</th>
              <th className="px-4 py-2">Current KM</th>
              <th className="px-4 py-2">Documents</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {vehicles.map((v) => {
              const expiringSoon =
                isExpiringOrExpired(v.insuranceExpiry) ||
                isExpiringOrExpired(v.fitnessExpiry) ||
                isExpiringOrExpired(v.taxTokenExpiry);
              return (
                <tr key={v.id} className="border-b border-slate-50 last:border-0">
                  <td className="px-4 py-2 font-medium text-slate-700">{v.registrationNumber}</td>
                  <td className="px-4 py-2 text-slate-700">{v.vehicleName}</td>
                  <td className="px-4 py-2 text-slate-500">{v.vehicleType}</td>
                  <td className="px-4 py-2 text-slate-500">{v.fuelType}</td>
                  <td className="px-4 py-2 text-slate-500">{deptName(v.assignedDepartmentId)}</td>
                  <td className="px-4 py-2 text-slate-500">{v.currentKm.toLocaleString()}</td>
                  <td className="px-4 py-2">
                    {expiringSoon ? (
                      <span className="inline-flex items-center gap-1 text-xs font-medium text-amber-600">
                        <AlertTriangle size={14} /> Expiring
                      </span>
                    ) : (
                      <span className="text-xs text-emerald-600">OK</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    <StatusBadge status={v.status} />
                  </td>
                  <td className="px-4 py-2">
                    <VehicleForm mode="edit" vehicle={v} departments={departments} />
                  </td>
                </tr>
              );
            })}
            {vehicles.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-sm text-slate-400">
                  No vehicles found for this range.
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
