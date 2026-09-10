import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData } from "@/lib/permissions";
import { expensesRepo, vehiclesRepo, bookingsRepo, usersRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { ExpenseForm } from "./expense-form";
import { DeleteExpenseButton } from "./delete-button";
import { ExpenseApprovalActions } from "./approval-actions";
import { FileText } from "lucide-react";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function ExpensesPage({
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
  const [allExpenses, vehicles, bookings, users] = await Promise.all([
    expensesRepo.findAll(),
    vehiclesRepo.findAll(),
    bookingsRepo.findAll(),
    usersRepo.findAll(),
  ]);
  const vehicleLabel = (id?: string) => (id ? vehicles.find((v) => v.id === id)?.registrationNumber || id : "—");
  const submitterName = (id: string) => users.find((u) => u.id === id)?.fullName || id;

  const scoped = isManager ? allExpenses : allExpenses.filter((e) => e.createdByUserId === session.userId);
  const filteredForTotal = filterByDateRange(scoped, "expenseDate", from, to);
  const total = filteredForTotal.filter((e) => e.approvalStatus === "APPROVED").reduce((sum, e) => sum + e.amount, 0);
  const sorted = filteredForTotal.sort((a, b) => b.expenseDate.localeCompare(a.expenseDate));
  const { items: expenses, totalPages, totalItems, page: currentPage } = paginate(sorted, Number(page) || 1);
  const pendingCount = allExpenses.filter((e) => e.approvalStatus === "PENDING").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Expenses</h1>
          <p className="text-sm text-slate-500">
            Fuel, service, repair, toll, tip and parking all live here as expense records. Approved total: BDT{" "}
            {total.toLocaleString()}
            {isManager && pendingCount > 0 && ` · ${pendingCount} pending approval`}
          </p>
        </div>
        <ExpenseForm vehicles={vehicles} bookings={bookings} isDriver={isDriver} />
      </div>

      <DateRangeFilter dateLabel="Expense date" />

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Expense ID</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Vehicle</th>
              <th className="px-4 py-2">Date</th>
              <th className="px-4 py-2">Amount (BDT)</th>
              <th className="px-4 py-2">Payment</th>
              {isManager && <th className="px-4 py-2">Submitted By</th>}
              <th className="px-4 py-2">Document</th>
              <th className="px-4 py-2">Approval</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {expenses.map((e) => (
              <tr key={e.id} className="border-b border-slate-50 last:border-0 align-top">
                <td className="px-4 py-2 font-medium text-slate-700">{e.id}</td>
                <td className="px-4 py-2 text-slate-600">{e.category}</td>
                <td className="px-4 py-2 text-slate-500">{vehicleLabel(e.vehicleId)}</td>
                <td className="px-4 py-2 text-slate-500">{e.expenseDate}</td>
                <td className="px-4 py-2 text-slate-500">{e.amount.toLocaleString()}</td>
                <td className="px-4 py-2 text-slate-500">{e.paymentMethod.replaceAll("_", " ")}</td>
                {isManager && <td className="px-4 py-2 text-slate-500">{submitterName(e.createdByUserId)}</td>}
                <td className="px-4 py-2">
                  {e.documentPath ? (
                    <a href={e.documentPath} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-medium text-indigo-600 hover:underline">
                      <FileText size={12} /> View
                    </a>
                  ) : (
                    <span className="text-xs text-slate-300">—</span>
                  )}
                </td>
                <td className="px-4 py-2">
                  <StatusBadge status={e.approvalStatus === "APPROVED" ? "APPROVED" : e.approvalStatus === "REJECTED" ? "REJECTED" : "PENDING"} />
                  {e.approvalStatus === "REJECTED" && e.approvalRejectionReason && (
                    <p className="mt-0.5 text-xs text-rose-500">{e.approvalRejectionReason}</p>
                  )}
                </td>
                <td className="px-4 py-2">
                  <div className="flex flex-col gap-1">
                    {isManager && e.approvalStatus === "PENDING" && <ExpenseApprovalActions id={e.id} />}
                    {isManager && <DeleteExpenseButton id={e.id} />}
                  </div>
                </td>
              </tr>
            ))}
            {expenses.length === 0 && (
              <tr>
                <td colSpan={isManager ? 9 : 8} className="px-4 py-6 text-center text-sm text-slate-400">
                  No expenses found for this range.
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
