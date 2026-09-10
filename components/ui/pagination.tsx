"use client";

import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function Pagination({ page, totalPages, totalItems }: { page: number; totalPages: number; totalItems: number }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function goTo(p: number) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(p));
    router.push(`${pathname}?${params.toString()}`);
  }

  if (totalPages <= 1) return null;

  // Show up to 5 page buttons centered around the current page.
  const pages: number[] = [];
  let start = Math.max(1, page - 2);
  const end = Math.min(totalPages, start + 4);
  start = Math.max(1, end - 4);
  for (let i = start; i <= end; i++) pages.push(i);

  return (
    <div className="flex flex-col items-center justify-between gap-3 border-t border-slate-100 px-4 py-3 sm:flex-row">
      <p className="text-xs text-slate-400">
        {totalItems} total {totalItems === 1 ? "item" : "items"}
      </p>
      <div className="flex flex-wrap items-center justify-center gap-1">
        <button
          onClick={() => goTo(page - 1)}
          disabled={page <= 1}
          className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          <ChevronLeft size={16} />
        </button>
        {start > 1 && (
          <>
            <PageButton n={1} active={false} onClick={() => goTo(1)} />
            {start > 2 && <span className="px-1 text-slate-300">…</span>}
          </>
        )}
        {pages.map((p) => (
          <PageButton key={p} n={p} active={p === page} onClick={() => goTo(p)} />
        ))}
        {end < totalPages && (
          <>
            {end < totalPages - 1 && <span className="px-1 text-slate-300">…</span>}
            <PageButton n={totalPages} active={false} onClick={() => goTo(totalPages)} />
          </>
        )}
        <button
          onClick={() => goTo(page + 1)}
          disabled={page >= totalPages}
          className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

function PageButton({ n, active, onClick }: { n: number; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={`h-8 w-8 shrink-0 rounded-lg text-xs font-medium transition-colors ${
        active ? "bg-indigo-600 text-white" : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      {n}
    </button>
  );
}
