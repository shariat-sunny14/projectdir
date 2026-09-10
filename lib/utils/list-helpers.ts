export const DEFAULT_PAGE_SIZE = 10;

export interface PaginationResult<T> {
  items: T[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
}

export function paginate<T>(items: T[], page: number, pageSize: number = DEFAULT_PAGE_SIZE): PaginationResult<T> {
  const totalItems = items.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safePage = Math.min(Math.max(1, page || 1), totalPages);
  const start = (safePage - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    page: safePage,
    pageSize,
    totalItems,
    totalPages,
  };
}

/** Filters a list by an ISO date/datetime string field against an optional
 * inclusive [from, to] range (both plain "yyyy-mm-dd" dates). */
export function filterByDateRange<T>(items: T[], dateField: keyof T, from?: string, to?: string): T[] {
  if (!from && !to) return items;
  const fromTime = from ? new Date(from + "T00:00:00").getTime() : -Infinity;
  const toTime = to ? new Date(to + "T23:59:59").getTime() : Infinity;
  return items.filter((item) => {
    const raw = item[dateField];
    if (!raw) return false;
    const t = new Date(String(raw)).getTime();
    if (Number.isNaN(t)) return false;
    return t >= fromTime && t <= toTime;
  });
}

/** Groups timestamped records into day/week/month buckets depending on the span of the
 * range, for a trend chart. Buckets with zero records are still included, in order. */
export function bucketTimeSeries(
  dates: string[],
  fromIso: string,
  toIso: string
): { label: string; count: number }[] {
  const from = new Date(fromIso + "T00:00:00");
  const to = new Date(toIso + "T23:59:59");
  const spanDays = Math.max(1, Math.round((to.getTime() - from.getTime()) / 86_400_000));

  const granularity: "day" | "week" | "month" = spanDays <= 31 ? "day" : spanDays <= 180 ? "week" : "month";

  // Local-calendar-date key (not toISOString, which converts to UTC first and
  // silently shifts the date by a day on any server whose timezone is ahead of
  // UTC — e.g. Asia/Dhaka — causing every count to land in a bucket that was
  // never created).
  function toLocalDateKey(d: Date): string {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }

  function bucketKey(d: Date): string {
    if (granularity === "day") return toLocalDateKey(d);
    if (granularity === "month") return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    // week: label by the Monday of that week
    const day = new Date(d);
    const dow = (day.getDay() + 6) % 7; // Mon=0..Sun=6
    day.setDate(day.getDate() - dow);
    return toLocalDateKey(day);
  }

  function bucketLabel(key: string): string {
    if (granularity === "month") {
      const [y, m] = key.split("-").map(Number);
      return new Date(y, m - 1, 1).toLocaleDateString("en-US", { month: "short", year: "2-digit" });
    }
    const d = new Date(key + "T00:00:00");
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }

  // Build ordered bucket keys spanning the whole range so empty buckets show as 0.
  const keys: string[] = [];
  const cursor = new Date(from);
  while (cursor <= to) {
    const key = bucketKey(cursor);
    if (keys[keys.length - 1] !== key) keys.push(key);
    if (granularity === "day") cursor.setDate(cursor.getDate() + 1);
    else if (granularity === "week") cursor.setDate(cursor.getDate() + 7);
    else cursor.setMonth(cursor.getMonth() + 1);
  }

  const counts = new Map<string, number>(keys.map((k) => [k, 0]));
  for (const dateStr of dates) {
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) continue;
    const key = bucketKey(d);
    if (counts.has(key)) counts.set(key, (counts.get(key) || 0) + 1);
  }

  return keys.map((k) => ({ label: bucketLabel(k), count: counts.get(k) || 0 }));
}
