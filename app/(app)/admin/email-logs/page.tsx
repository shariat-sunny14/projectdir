import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { isAdmin } from "@/lib/permissions";
import { emailLogsRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { ResendButton } from "./resend-button";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function EmailLogsPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!isAdmin(session.role)) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const allLogs = await emailLogsRepo.findAll();
  const sentCount = allLogs.filter((l) => l.status === "SENT").length;
  const failedCount = allLogs.filter((l) => l.status === "FAILED").length;
  const filtered = filterByDateRange(allLogs, "createdAt", from, to).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  const { items: logs, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(page) || 1);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Email Logs</h1>
        <p className="text-sm text-slate-500">
          Every email sent by the system, via Gmail SMTP.{" "}
          <span className="font-medium text-emerald-600">{sentCount} sent</span>
          {failedCount > 0 && (
            <>
              {" · "}
              <span className="font-medium text-rose-600">{failedCount} failed</span>
            </>
          )}
        </p>
      </div>

      <DateRangeFilter dateLabel="Sent" />

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Log ID</th>
              <th className="px-4 py-2">To</th>
              <th className="px-4 py-2">Event</th>
              <th className="px-4 py-2">Subject</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Sent At</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-b border-slate-50 last:border-0 align-top">
                <td className="px-4 py-2 font-medium text-slate-700">{l.id}</td>
                <td className="px-4 py-2 text-slate-600">{l.to}</td>
                <td className="px-4 py-2 text-slate-500">{l.event}</td>
                <td className="px-4 py-2 text-slate-500">
                  {l.subject}
                  {l.status === "FAILED" && l.errorMessage && (
                    <p className="mt-0.5 text-xs text-rose-500">{l.errorMessage}</p>
                  )}
                </td>
                <td className="px-4 py-2">
                  <StatusBadge status={l.status} />
                </td>
                <td className="px-4 py-2 text-slate-400">{new Date(l.createdAt).toLocaleString()}</td>
                <td className="px-4 py-2">
                  <ResendButton logId={l.id} />
                </td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-6 text-center text-sm text-slate-400">
                  No emails found for this range.
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
