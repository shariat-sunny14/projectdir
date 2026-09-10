import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { isAdmin } from "@/lib/permissions";
import { usersRepo, departmentsRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApprovalRow } from "./approval-row";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function UserApprovalsPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!isAdmin(session.role)) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const [users, departments] = await Promise.all([usersRepo.findAll(), departmentsRepo.findAll()]);
  const pending = users.filter((u) => u.status === "PENDING").sort((a, b) => a.createdAt.localeCompare(b.createdAt));
  const othersAll = users.filter((u) => u.status !== "PENDING").sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
  const othersFiltered = filterByDateRange(othersAll, "updatedAt", from, to);
  const { items: others, totalPages, totalItems, page: currentPage } = paginate(othersFiltered, Number(page) || 1);

  const deptName = (id?: string) => departments.find((d) => d.id === id)?.name || "—";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">User Approvals</h1>
        <p className="text-sm text-slate-500">Review new sign-ups and approve or reject access.</p>
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="font-semibold text-slate-900">Pending ({pending.length})</h2>
        </div>
        {pending.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-400">No pending approvals.</p>
        ) : (
          <div className="divide-y divide-slate-100">
            {pending.map((u) => (
              <ApprovalRow key={u.id} user={u} departmentName={deptName(u.departmentId)} />
            ))}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <div className="border-b border-slate-200 px-4 py-3">
          <h2 className="font-semibold text-slate-900">History</h2>
        </div>
        <div className="border-b border-slate-100 px-4 py-3">
          <DateRangeFilter dateLabel="Decision date" />
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Department</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {others.map((u) => (
              <tr key={u.id} className="border-b border-slate-50 last:border-0">
                <td className="px-4 py-2 font-medium text-slate-700">{u.fullName}</td>
                <td className="px-4 py-2 text-slate-500">{u.email}</td>
                <td className="px-4 py-2 text-slate-500">{deptName(u.departmentId)}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={u.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {others.length === 0 && <p className="px-4 py-6 text-center text-sm text-slate-400">No history found for this range.</p>}
        <Pagination page={currentPage} totalPages={totalPages} totalItems={totalItems} />
      </div>
    </div>
  );
}
