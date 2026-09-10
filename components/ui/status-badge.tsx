const STYLES: Record<string, string> = {
  ACTIVE: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  AVAILABLE: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  APPROVED: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  COMPLETED: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  SENT: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  OPEN: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  PENDING: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  BOOKED: "bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-200",
  ON_TRIP: "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200",
  MAINTENANCE: "bg-orange-50 text-orange-700 ring-1 ring-inset ring-orange-200",
  OFF_DUTY: "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-200",
  REJECTED: "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200",
  FAILED: "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200",
  CANCELLED: "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200",
  SUSPENDED: "bg-rose-50 text-rose-700 ring-1 ring-inset ring-rose-200",
  INACTIVE: "bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-200",
};

export function StatusBadge({ status }: { status: string }) {
  const style = STYLES[status] || "bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200";
  return <span className={`badge ${style}`}>{status.replaceAll("_", " ")}</span>;
}
