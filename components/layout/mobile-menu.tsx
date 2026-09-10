"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, X, LogOut } from "lucide-react";
import { logoutAction } from "@/lib/actions/auth-actions";
import type { Role } from "@/lib/types";
import { buildNav, type NavItem } from "@/lib/nav-config";

function DrawerLink({ item, active, onNavigate }: { item: NavItem; active: boolean; onNavigate: () => void }) {
  const Icon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
        active ? "bg-indigo-50 text-indigo-600" : "text-slate-600 hover:bg-slate-100"
      }`}
    >
      <Icon size={18} className={active ? "text-indigo-600" : "text-slate-400"} />
      {item.label}
    </Link>
  );
}

export function MobileMenu({ role }: { role: Role }) {
  const [open, setOpen] = useState(false);
  // Portals need a browser document, so only render the portal after mount.
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();
  const sections = buildNav(role);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close the drawer whenever the route changes (e.g. back/forward navigation).
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Prevent background scrolling while the drawer is open.
  useEffect(() => {
    if (open) {
      const previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = previousOverflow;
      };
    }
  }, [open]);

  // Close on Escape key for accessibility.
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open]);

  const drawer = (
    <div className="fixed inset-0 z-[100]">
      {/* Overlay */}
      <button
        type="button"
        aria-label="Close menu"
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-[1px]"
        onClick={() => setOpen(false)}
      />

      {/* Drawer panel */}
      <div className="absolute inset-y-0 left-0 flex h-full w-[82%] max-w-xs flex-col bg-white shadow-xl animate-slide-in-left">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-base font-bold text-white shadow-sm">
              F
            </div>
            <div>
              <p className="text-sm font-semibold leading-tight text-slate-800">Fleet</p>
              <p className="text-[11px] leading-tight text-slate-400">Management Suite</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
          {sections.map((section, i) => (
            <div key={i}>
              {section.title && (
                <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                  {section.title}
                </p>
              )}
              <div className="flex flex-col gap-0.5">
                {section.items.map((item) => (
                  <DrawerLink
                    key={item.href}
                    item={item}
                    active={pathname === item.href || pathname.startsWith(item.href + "/")}
                    onNavigate={() => setOpen(false)}
                  />
                ))}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-slate-100 p-3">
          <p className="mb-2 px-2 text-[11px] text-slate-400">
            Signed in as <span className="font-medium text-slate-500">{role.replaceAll("_", " ")}</span>
          </p>
          <form action={logoutAction}>
            <button
              type="submit"
              className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50"
            >
              <LogOut size={18} />
              Logout
            </button>
          </form>
        </div>
      </div>
    </div>
  );

  return (
    <div className="md:hidden">
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open menu"
        aria-expanded={open}
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
      >
        <Menu size={22} />
      </button>

      {/*
        Rendered via a portal directly into document.body.
        Why: the Header uses `backdrop-blur` (a CSS filter), and any element with
        a filter/backdrop-filter/transform becomes the "containing block" for its
        `position: fixed` descendants. Without the portal, this drawer would be
        fixed relative to the (short, 64px) Header instead of the viewport —
        which is exactly why it was appearing squeezed/hidden behind the page
        content instead of as a full-height overlay.
      */}
      {mounted && open ? createPortal(drawer, document.body) : null}
    </div>
  );
}
