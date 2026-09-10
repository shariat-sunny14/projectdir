import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData } from "@/lib/permissions";
import { departmentsRepo, usersRepo } from "@/lib/json-db/repositories";
import { StatusBadge } from "@/components/ui/status-badge";
import { DepartmentForm } from "./department-form";
import { DepartmentStatusToggle } from "./department-status-toggle";
import { DateRangeFilter } from "@/components/ui/date-range-filter";
import { Pagination } from "@/components/ui/pagination";
import { filterByDateRange, paginate } from "@/lib/utils/list-helpers";

export default async function DepartmentsPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string; to?: string; page?: string }>;
}) {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!canManageMasterData(session.role)) redirect("/dashboard");

  const { from, to, page } = await searchParams;
  const [allDepartments, users] = await Promise.all([departmentsRepo.findAll(), usersRepo.findAll()]);
  const employeeCount = (deptId: string) => users.filter((u) => u.departmentId === deptId).length;
  const filtered = filterByDateRange(allDepartments, "createdAt", from, to).sort((a, b) => a.name.localeCompare(b.name));
  const { items: departments, totalPages, totalItems, page: currentPage } = paginate(filtered, Number(page) || 1);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Departments</h1>
          <p className="text-sm text-slate-500">Manage the departments employees belong to.</p>
        </div>
        <DepartmentForm mode="create" />
      </div>

      <DateRangeFilter dateLabel="Added" />

      <div className="rounded-2xl border border-slate-200/80 bg-white shadow-sm shadow-slate-200/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <th className="px-4 py-2">Code</th>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Manager</th>
              <th className="px-4 py-2">Employees</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {departments.map((d) => (
              <tr key={d.id} className="border-b border-slate-50 last:border-0">
                <td className="px-4 py-2 font-medium text-slate-700">{d.code}</td>
                <td className="px-4 py-2 text-slate-700">{d.name}</td>
                <td className="px-4 py-2 text-slate-500">{d.manager || "—"}</td>
                <td className="px-4 py-2 text-slate-500">{employeeCount(d.id)}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={d.status} />
                </td>
                <td className="px-4 py-2">
                  <div className="flex items-center gap-3">
                    <DepartmentForm mode="edit" department={d} />
                    <DepartmentStatusToggle
                      id={d.id}
                      status={d.status}
                      disabled={employeeCount(d.id) > 0 && d.status === "ACTIVE"}
                    />
                  </div>
                </td>
              </tr>
            ))}
            {departments.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-slate-400">
                  No departments found for this range.
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
