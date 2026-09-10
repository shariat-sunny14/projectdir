"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Car, Clock, Navigation2, RadioTower } from "lucide-react";
import { MapView } from "@/components/ui/map-view";
import { getActiveTrackingAction } from "@/lib/actions/tracking-actions";
import type { ActiveTrackedVehicle } from "@/lib/services/tracking-service";

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 5000) return "just now";
  if (diff < 60000) return `${Math.round(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
  return new Date(iso).toLocaleTimeString();
}

const PALETTE = ["#2563eb", "#7c3aed", "#059669", "#d97706", "#db2777", "#0891b2"];

export function LiveTrackingMap({ initial }: { initial: ActiveTrackedVehicle[] }) {
  const [vehicles, setVehicles] = useState<ActiveTrackedVehicle[]>(initial);
  const [, forceTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      const data = await getActiveTrackingAction();
      if (!cancelled) setVehicles(data);
    }
    const interval = setInterval(poll, 8000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    const t = setInterval(() => forceTick((n) => n + 1), 5000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <div className="order-2 space-y-3 lg:order-1 lg:col-span-1">
        <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
          <RadioTower size={16} className="text-emerald-600" />
          {vehicles.length} vehicle{vehicles.length === 1 ? "" : "s"} currently on trip
        </div>

        {vehicles.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-center text-sm text-slate-400">
            No vehicle is on an active trip right now.
          </p>
        ) : (
          <div className="space-y-3">
            {vehicles.map((v, i) => (
              <Link
                key={v.vehicleId}
                href={`/bookings/${v.bookingId}`}
                className="block rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50 transition-colors hover:border-indigo-300"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-medium text-slate-800">
                    <Car size={16} style={{ color: PALETTE[i % PALETTE.length] }} />
                    {v.vehicleName}
                  </div>
                  <span className="badge bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200">
                    <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                    LIVE
                  </span>
                </div>
                <p className="mt-1 text-xs text-slate-500">{v.registrationNumber} · Driver: {v.driverName}</p>
                <p className="mt-1.5 flex items-center gap-1.5 text-xs text-slate-500">
                  <Navigation2 size={12} /> {v.pickupLocation} → {v.destinationLocation}
                </p>
                <p className="mt-1 flex items-center gap-1.5 text-[11px] text-slate-400">
                  <Clock size={11} /> Updated {timeAgo(v.updatedAt)} · Booking {v.bookingId}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>

      <div className="order-1 lg:order-2 lg:col-span-2">
        <MapView
          height="520px"
          zoom={12}
          markers={vehicles.map((v, i) => ({
            id: v.vehicleId,
            lat: v.lat,
            lng: v.lng,
            color: PALETTE[i % PALETTE.length],
            pulse: true,
            popupHtml: `<strong>${v.vehicleName}</strong> (${v.registrationNumber})<br/>Driver: ${v.driverName}<br/>${v.pickupLocation} → ${v.destinationLocation}<br/>Booking ${v.bookingId}`,
          }))}
        />
      </div>
    </div>
  );
}
