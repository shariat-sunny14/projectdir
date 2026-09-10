import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData } from "@/lib/permissions";
import { maintenanceRepo, vehiclesRepo, usersRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { MaintenanceForm } from "./maintenance-form";
import { CompleteMaintenanceButton } from "./complete-button";
import { MaintenanceApprovalActions } from "./approval-actions";
import { FileText } from "lucide-react";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function MaintenancePage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  const isManager = canManageMasterData(session.role);
  const isDriver = session.role === "DRIVER";
  if (!isManager && !isDriver) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const [allRecords, vehicles, users] = await Promise.all([maintenanceRepo.findAll(), vehiclesRepo.findAll(), usersRepo.findAll()]);
  const vehicleLabel = (id: string) => vehicles.find((v) => v.id === id)?.registrationNumber || id;
  const submitterName = (id?: string) => (id ? users.find((u) => u.id === id)?.fullName || id : "—");

  const scoped = isManager ? allRecords : allRecords.filter((r) => r.submittedByUserId === session.userId);
  const filtered = filterByDateRange(scoped, "serviceDate", from, to).sort((a, b) => b.serviceDate.localeCompare(a.serviceDate));
  const { items: sorted, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(page) || 1);
  const pendingCount = allRecords.filter((r) => r.approvalStatus === "PENDING").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Service / Maintenance</h1>
          <p className="text-sm text-slate-500">
            {isManager
              ? `Open service records put the vehicle into Maintenance and block new bookings until completed.${pendingCount > 0 ? ` ${pendingCount} entr${pendingCount === 1 ? "y" : "ies"} awaiting your approval.` : ""}`
              : "Your submitted service entries. An admin will review and approve them."}
          </p>
        </div>
        <MaintenanceForm vehicles={vehicles} isDriver={isDriver} />
      </div>

      <DateRangeFilter dateLabel="Service date" />

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Service ID</th>
              <th className="px-4 py-2">Vehicle</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Date</th>
              <th className="px-4 py-2">Total Cost (BDT)</th>
              {isManager && <th className="px-4 py-2">Submitted By</th>}
              <th className="px-4 py-2">Document</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Approval</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.id} className="border-b border-slate-50 last:border-0 align-top">
                <td className="px-4 py-2 font-medium text-slate-700">{r.id}</td>
                <td className="px-4 py-2 text-slate-600">{vehicleLabel(r.vehicleId)}</td>
                <td className="px-4 py-2 text-slate-500">{r.serviceType}</td>
                <td className="px-4 py-2 text-slate-500">{r.serviceDate}</td>
                <td className="px-4 py-2 text-slate-500">{r.totalCost.toLocaleString()}</td>
                {isManager && <td className="px-4 py-2 text-slate-500">{submitterName(r.submittedByUserId)}</td>}
                <td className="px-4 py-2">
                  {r.documentPath ? (
                    <a href={r.documentPath} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:underline">
                      <FileText size={12} /> View
                    </a>
                  ) : (
                    <span className="text-xs text-slate-300">—</span>
                  )}
                </td>
                <td className="px-4 py-2">
                  <StatusBadge status={r.status} />
                </td>
                <td className="px-4 py-2">
                  <StatusBadge status={r.approvalStatus === "APPROVED" ? "APPROVED" : r.approvalStatus === "REJECTED" ? "REJECTED" : "PENDING"} />
                  {r.approvalStatus === "REJECTED" && r.approvalRejectionReason && (
                    <p className="mt-0.5 text-xs text-rose-500">{r.approvalRejectionReason}</p>
                  )}
                </td>
                <td className="px-4 py-2">
                  <div className="flex flex-col gap-1">
                    {isManager && r.approvalStatus === "PENDING" && <MaintenanceApprovalActions id={r.id} />}
                    {isManager && r.approvalStatus === "APPROVED" && r.status === "OPEN" && <CompleteMaintenanceButton id={r.id} />}
                  </div>
                </td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={isManager ? 10 : 9} className="px-4 py-6 text-center text-sm text-slate-400">
                  No service records found for this range.
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
