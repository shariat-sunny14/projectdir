import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { isAdmin } from "@/lib/permissions";
import { auditLogsRepo, usersRepo } from "@/lib/json-db/repositories";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function AuditLogsPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!isAdmin(session.role)) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const [allLogs, users] = await Promise.all([auditLogsRepo.findAll(), usersRepo.findAll()]);
  const filtered = filterByDateRange(allLogs, "createdAt", from, to).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const { items: sorted, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(page) || 1);
  const actorName = (id: string) => users.find((u) => u.id === id)?.fullName || id;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Audit Logs</h1>
        <p className="text-sm text-slate-500">System-wide record of user, booking, trip, and master-data changes.</p>
      </div>

      <DateRangeFilter dateLabel="Date" />

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Log ID</th>
              <th className="px-4 py-2">User</th>
              <th className="px-4 py-2">Module</th>
              <th className="px-4 py-2">Action</th>
              <th className="px-4 py-2">Record</th>
              <th className="px-4 py-2">Description</th>
              <th className="px-4 py-2">When</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((l) => (
              <tr key={l.id} className="border-b border-slate-50 last:border-0">
                <td className="px-4 py-2 font-medium text-slate-700">{l.id}</td>
                <td className="px-4 py-2 text-slate-600">{actorName(l.userId)}</td>
                <td className="px-4 py-2 text-slate-500">{l.module}</td>
                <td className="px-4 py-2 text-slate-500">{l.action.replaceAll("_", " ")}</td>
                <td className="px-4 py-2 text-slate-500">{l.recordId}</td>
                <td className="px-4 py-2 text-slate-500">{l.description || "—"}</td>
                <td className="px-4 py-2 text-slate-400">{new Date(l.createdAt).toLocaleString()}</td>
              </tr>
            ))}
            {sorted.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-sm text-slate-400">
                  No audit events found for this range.
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
