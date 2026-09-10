import { redirect } from "next/navigation";
import { getSession } from "@/lib/auth/session";
import { canManageMasterData } from "@/lib/permissions";
import {
  expensesRepo,
  bookingsRepo,
  vehiclesRepo,
  driversRepo,
  usersRepo,
  departmentsRepo,
  maintenanceRepo,
  tripsRepo,
} from "@/lib/json-db/repositories";
import type { ExpenseCategory } from "@/lib/types";

const EXPENSE_CATEGORIES: ExpenseCategory[] = ["FUEL", "TOLL", "TIP", "PARKING", "REPAIR", "SERVICE", "INSURANCE", "TAX", "OTHER"];

export default async function ReportsPage() {
  const session = await getSession();
  if (!session) redirect("/login");
  if (!canManageMasterData(session.role)) redirect("/dashboard");

  const [expenses, bookings, vehicles, drivers, users, departments, maintenance, trips] = await Promise.all([
    expensesRepo.findAll(),
    bookingsRepo.findAll(),
    vehiclesRepo.findAll(),
    driversRepo.findAll(),
    usersRepo.findAll(),
    departmentsRepo.findAll(),
    maintenanceRepo.findAll(),
    tripsRepo.findAll(),
  ]);

  // 21.2 Vehicle Expense Report — by category, by vehicle
  const expenseByCategory = EXPENSE_CATEGORIES.map((c) => ({
    category: c,
    total: expenses.filter((e) => e.category === c).reduce((s, e) => s + e.amount, 0),
  }));
  const maxCategoryTotal = Math.max(1, ...expenseByCategory.map((c) => c.total));

  // 21.1 Vehicle Usage Report
  const vehicleUsage = vehicles.map((v) => {
    const vBookings = bookings.filter((b) => b.assignedVehicleId === v.id);
    const vTrips = trips.filter((t) => t.vehicleId === v.id && t.status === "COMPLETED");
    const totalKm = vTrips.reduce((s, t) => s + (t.totalKm ?? 0), 0);
    return { vehicle: v, totalBookings: vBookings.length, totalTrips: vTrips.length, totalKm };
  });

  // 21.3 Driver Report
  const driverReport = drivers.map((d) => {
    const dTrips = trips.filter((t) => t.driverId === d.id);
    const completed = dTrips.filter((t) => t.status === "COMPLETED");
    const totalKm = completed.reduce((s, t) => s + (t.totalKm ?? 0), 0);
    return { driver: d, totalTrips: dTrips.length, completedTrips: completed.length, totalKm };
  });

  // 21.4 Employee Booking Report
  const employees = users.filter((u) => u.role === "EMPLOYEE" || u.role === "DRIVER" ? u.role === "EMPLOYEE" : true).filter((u) => u.status === "ACTIVE");
  const employeeReport = employees
    .map((e) => {
      const eBookings = bookings.filter((b) => b.employeeId === e.id);
      return {
        employee: e,
        department: departments.find((d) => d.id === e.departmentId)?.name || "—",
        total: eBookings.length,
        completed: eBookings.filter((b) => b.status === "COMPLETED").length,
        cancelled: eBookings.filter((b) => b.status === "CANCELLED").length,
        rejected: eBookings.filter((b) => b.status === "REJECTED").length,
      };
    })
    .filter((r) => r.total > 0);

  // 21.5 Monthly Expense Report (last 6 months)
  const months: { key: string; label: string }[] = [];
  const now = new Date();
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    months.push({ key: `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`, label: d.toLocaleString("default", { month: "short", year: "2-digit" }) });
  }
  const monthlyReport = months.map(({ key, label }) => {
    const monthExpenses = expenses.filter((e) => e.expenseDate.startsWith(key));
    const byCat = (cats: ExpenseCategory[]) => monthExpenses.filter((e) => cats.includes(e.category)).reduce((s, e) => s + e.amount, 0);
    return {
      label,
      fuel: byCat(["FUEL"]),
      maintenance: byCat(["SERVICE", "REPAIR"]),
      toll: byCat(["TOLL"]),
      parking: byCat(["PARKING"]),
      tip: byCat(["TIP"]),
      other: byCat(["INSURANCE", "TAX", "OTHER"]),
      total: monthExpenses.reduce((s, e) => s + e.amount, 0),
    };
  });

  // 21.6 Service Report
  const serviceReport = vehicles.map((v) => {
    const records = maintenance.filter((m) => m.vehicleId === v.id).sort((a, b) => b.serviceDate.localeCompare(a.serviceDate));
    const last = records[0];
    return { vehicle: v, last };
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">Reports</h1>
        <p className="text-sm text-slate-500">Basic operational summaries derived from current data.</p>
      </div>

      <ReportCard title="Vehicle Expense Report (by Category, BDT)">
        <div className="space-y-2">
          {expenseByCategory.map((c) => (
            <div key={c.category} className="flex items-center gap-3">
              <span className="w-20 text-xs text-slate-500">{c.category}</span>
              <div className="h-3 flex-1 rounded-full bg-slate-100">
                <div className="h-3 rounded-full bg-indigo-500" style={{ width: `${(c.total / maxCategoryTotal) * 100}%` }} />
              </div>
              <span className="w-20 text-right text-xs text-slate-500">{c.total.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </ReportCard>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <ReportCard title="Vehicle Usage Report">
          <Table
            headers={["Vehicle", "Bookings", "Trips", "Total KM"]}
            rows={vehicleUsage.map((r) => [r.vehicle.registrationNumber, String(r.totalBookings), String(r.totalTrips), r.totalKm.toLocaleString()])}
          />
        </ReportCard>

        <ReportCard title="Driver Report">
          <Table
            headers={["Driver", "Total Trips", "Completed", "Total KM"]}
            rows={driverReport.map((r) => [r.driver.driverName, String(r.totalTrips), String(r.completedTrips), r.totalKm.toLocaleString()])}
          />
        </ReportCard>

        <ReportCard title="Employee Booking Report">
          <Table
            headers={["Employee", "Department", "Total", "Completed", "Cancelled", "Rejected"]}
            rows={employeeReport.map((r) => [r.employee.fullName, r.department, String(r.total), String(r.completed), String(r.cancelled), String(r.rejected)])}
          />
        </ReportCard>

        <ReportCard title="Service Report">
          <Table
            headers={["Vehicle", "Last Service", "Current KM", "Next Service", "Service Cost"]}
            rows={serviceReport.map((r) => [
              r.vehicle.registrationNumber,
              r.last?.serviceDate || "—",
              r.vehicle.currentKm.toLocaleString(),
              r.last?.nextServiceDate || "—",
              r.last ? r.last.totalCost.toLocaleString() : "—",
            ])}
          />
        </ReportCard>
      </div>

      <ReportCard title="Monthly Expense Report (last 6 months, BDT)">
        <div className="overflow-x-auto">
          <Table
            headers={["Month", "Fuel", "Maintenance", "Toll", "Parking", "Tip", "Other", "Total"]}
            rows={monthlyReport.map((m) => [
              m.label,
              m.fuel.toLocaleString(),
              m.maintenance.toLocaleString(),
              m.toll.toLocaleString(),
              m.parking.toLocaleString(),
              m.tip.toLocaleString(),
              m.other.toLocaleString(),
              m.total.toLocaleString(),
            ])}
          />
        </div>
      </ReportCard>
    </div>
  );
}

function ReportCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
      <h2 className="mb-4 font-semibold text-slate-900">{title}</h2>
      {children}
    </div>
  );
}

function Table({ headers, rows }: { headers: string[]; rows: string[][] }) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-400">No data yet.</p>;
  }
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-slate-100 bg-slate-50/60 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {headers.map((h) => (
            <th key={h} className="py-1.5 pr-4">
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row, i) => (
          <tr key={i} className="border-b border-slate-50 last:border-0">
            {row.map((cell, j) => (
              <td key={j} className={`py-1.5 pr-4 ${j === 0 ? "font-medium text-slate-700" : "text-slate-600"}`}>
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
