import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData, isAdmin } from "@/lib/permissions";
import { usersRepo, departmentsRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { EmployeeStatusActions } from "./employee-status-actions";
import { EmployeeEditForm } from "./employee-edit-form";
import { EmployeeCreateForm } from "./employee-create-form";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function EmployeesPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!canManageMasterData(session.role)) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const [users, departments] = await Promise.all([usersRepo.findAll(), departmentsRepo.findAll()]);
  const deptName = (id?: string) => departments.find((d) => d.id === id)?.name || "—";
  const scoped = users.filter((u) => u.status !== "PENDING" && u.status !== "REJECTED");
  const filtered = filterByDateRange(scoped, "createdAt", from, to).sort((a, b) => a.fullName.localeCompare(b.fullName));
  const { items: employees, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(page) || 1);

  const canEditRole = isAdmin(session.role);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Employees</h1>
          <p className="text-sm text-slate-500">
            All active and suspended user accounts. New employees join via Sign Up, or you can add one directly.
            {canEditRole && " As an admin, you can also edit their role here."}
          </p>
        </div>
        <EmployeeCreateForm departments={departments} canAssignAnyRole={canEditRole} />
      </div>

      <DateRangeFilter dateLabel="Joined" />

      <div className="overflow-x-auto rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Employee ID</th>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Phone</th>
              <th className="px-4 py-2">Department</th>
              <th className="px-4 py-2">Designation</th>
              <th className="px-4 py-2">Role</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((u) => (
              <tr key={u.id} className="border-b border-slate-50 last:border-0">
                <td className="px-4 py-2 font-medium text-slate-700">{u.employeeId || u.id}</td>
                <td className="px-4 py-2 text-slate-700">{u.fullName}</td>
                <td className="px-4 py-2 text-slate-500">{u.email}</td>
                <td className="px-4 py-2 text-slate-500">{u.phone}</td>
                <td className="px-4 py-2 text-slate-500">{deptName(u.departmentId)}</td>
                <td className="px-4 py-2 text-slate-500">{u.designation || "—"}</td>
                <td className="px-4 py-2 text-slate-500">{u.role.replaceAll("_", " ")}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={u.status} />
                </td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-3">
                    <EmployeeEditForm user={u} departments={departments} canEditRole={canEditRole} isSelf={u.id === session.userId} />
                    <EmployeeStatusActions id={u.id} status={u.status} />
                  </div>
                </td>
              </tr>
            ))}
            {employees.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-6 text-center text-sm text-slate-400">
                  No employees found for this range.
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
