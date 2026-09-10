"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  BarChart,
  Bar,
} from "recharts";

const STATUS_COLORS: Record<string, string> = {
  AVAILABLE: "#10b981",
  BOOKED: "#f59e0b",
  ON_TRIP: "#3b82f6",
  MAINTENANCE: "#f97316",
  INACTIVE: "#94a3b8",
};

const CATEGORY_COLOR = "#6366f1";

function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/50">
      <div className="mb-4">
        <h3 className="font-semibold text-slate-900">{title}</h3>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}

function TooltipCard({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; color?: string }>; label?: string }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs shadow-lg">
      {label && <p className="mb-1 font-semibold text-slate-700">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }} className="font-medium">
          {p.name}: {p.value.toLocaleString()}
        </p>
      ))}
    </div>
  );
}

export function BookingsTrendChart({ data }: { data: { label: string; count: number }[] }) {
  return (
    <ChartCard title="Bookings Trend" subtitle="New booking requests over the selected period">
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="bookingsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
          <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} allowDecimals={false} width={30} />
          <Tooltip content={<TooltipCard />} />
          <Area
            type="monotone"
            dataKey="count"
            name="Bookings"
            stroke="#6366f1"
            strokeWidth={2.5}
            fill="url(#bookingsGradient)"
            activeDot={{ r: 5 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export function VehicleStatusChart({ data }: { data: { name: string; value: number }[] }) {
  const nonZero = data.filter((d) => d.value > 0);
  return (
    <ChartCard title="Vehicle Status" subtitle="Current fleet distribution">
      {nonZero.length === 0 ? (
        <div className="flex h-[260px] items-center justify-center text-sm text-slate-400">No vehicles yet.</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={nonZero} dataKey="value" nameKey="name" innerRadius={62} outerRadius={92} paddingAngle={3} cornerRadius={6} strokeWidth={0}>
              {nonZero.map((entry) => (
                <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || "#cbd5e1"} />
              ))}
            </Pie>
            <Tooltip content={<TooltipCard />} />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              iconSize={8}
              formatter={(value) => <span className="text-xs text-slate-500">{String(value).replaceAll("_", " ")}</span>}
            />
          </PieChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}

export function ExpenseByCategoryChart({ data }: { data: { category: string; amount: number }[] }) {
  const nonZero = data.filter((d) => d.amount > 0);
  return (
    <ChartCard title="Expenses by Category" subtitle="Approved expenses (BDT) in the selected period">
      {nonZero.length === 0 ? (
        <div className="flex h-[260px] items-center justify-center text-sm text-slate-400">No expenses in this range.</div>
      ) : (
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={nonZero} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
            <XAxis type="number" tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="category" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} width={70} />
            <Tooltip content={<TooltipCard />} cursor={{ fill: "#f8fafc" }} />
            <Bar dataKey="amount" name="Amount" fill={CATEGORY_COLOR} radius={[0, 6, 6, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}
