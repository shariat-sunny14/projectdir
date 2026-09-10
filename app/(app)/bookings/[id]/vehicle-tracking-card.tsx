"use client";

import { useEffect, useRef, useState } from "react";
import { Radar, Satellite, TriangleAlert } from "lucide-react";
import { MapView } from "@/components/ui/map-view";
import { Button } from "@/components/ui/button";
import { pingVehicleLocationAction, getTripTrackingStatusAction, getTripLocationHistoryAction } from "@/lib/actions/tracking-actions";
import type { TripStatus, VehicleLocationPing } from "@/lib/types";

function timeAgo(iso: string | null): string {
  if (!iso) return "never";
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 5000) return "just now";
  if (diff < 60000) return `${Math.round(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.round(diff / 60000)}m ago`;
  return new Date(iso).toLocaleString();
}

/** Feature #14: live position while a trip is RUNNING (polled), plus the
 * full breadcrumb trail once a trip has COMPLETED. The driver-only "Share My
 * Location" toggle is what actually produces the pings via the browser's
 * Geolocation API. */
export function VehicleTrackingCard({
  tripId,
  isDriver,
  tripStatus,
  vehicleName,
}: {
  tripId: string;
  isDriver: boolean;
  tripStatus: TripStatus;
  vehicleName?: string;
}) {
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [tracking, setTracking] = useState(false);
  const [history, setHistory] = useState<VehicleLocationPing[]>([]);
  const [sharing, setSharing] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);
  const [, forceTick] = useState(0);
  const watchTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Live polling of the current position while the trip is running.
  useEffect(() => {
    if (tripStatus !== "RUNNING") return;
    let cancelled = false;
    async function poll() {
      const status = await getTripTrackingStatusAction(tripId);
      if (cancelled || !status) return;
      setLat(status.lat);
      setLng(status.lng);
      setUpdatedAt(status.updatedAt);
      setTracking(status.tracking);
    }
    poll();
    const interval = setInterval(poll, 8000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [tripId, tripStatus]);

  // History trail once the trip has finished.
  useEffect(() => {
    if (tripStatus !== "COMPLETED") return;
    getTripLocationHistoryAction(tripId).then(setHistory);
  }, [tripId, tripStatus]);

  // Re-render every 5s so the "x ago" label stays fresh without extra polling.
  useEffect(() => {
    const t = setInterval(() => forceTick((n) => n + 1), 5000);
    return () => clearInterval(t);
  }, []);

  // Stop the browser geolocation loop on unmount (trip completed / navigated away).
  useEffect(() => {
    return () => {
      if (watchTimerRef.current) clearInterval(watchTimerRef.current);
    };
  }, []);

  function sendPing() {
    if (!navigator.geolocation) {
      setGeoError("Geolocation isn't supported on this device.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const result = await pingVehicleLocationAction(tripId, pos.coords.latitude, pos.coords.longitude);
        if (!result.ok) {
          setGeoError(result.error.message);
          setSharing(false);
          if (watchTimerRef.current) clearInterval(watchTimerRef.current);
          return;
        }
        setGeoError(null);
        setLat(pos.coords.latitude);
        setLng(pos.coords.longitude);
        setUpdatedAt(new Date().toISOString());
        setTracking(true);
      },
      (err) => setGeoError(err.message || "Couldn't read your location."),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  function toggleSharing() {
    if (sharing) {
      setSharing(false);
      if (watchTimerRef.current) clearInterval(watchTimerRef.current);
      return;
    }
    setGeoError(null);
    setSharing(true);
    sendPing();
    watchTimerRef.current = setInterval(sendPing, 15000);
  }

  if (tripStatus === "COMPLETED") {
    const points = history.map((h) => ({ lat: h.lat, lng: h.lng }));
    return (
      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-semibold text-slate-900">Vehicle Tracking History</h2>
          <span className="badge bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-200">{points.length} points recorded</span>
        </div>
        {points.length >= 2 ? (
          <MapView
            height="240px"
            markers={[
              { id: "start", lat: points[0].lat, lng: points[0].lng, color: "#059669", label: "S", popupHtml: "Trip start" },
              { id: "end", lat: points[points.length - 1].lat, lng: points[points.length - 1].lng, color: "#e11d48", label: "E", popupHtml: "Trip end" },
            ]}
            path={points}
          />
        ) : (
          <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-400">
            No GPS history was recorded for this trip.
          </p>
        )}
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 font-semibold text-slate-900">
          <Radar size={17} className={tracking ? "text-emerald-600" : "text-slate-400"} />
          Live Vehicle Tracking {vehicleName ? `— ${vehicleName}` : ""}
        </h2>
        <span
          className={`badge ${tracking ? "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200" : "bg-slate-100 text-slate-500 ring-1 ring-inset ring-slate-200"}`}
        >
          {tracking && <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />}
          {tracking ? "LIVE" : "Not tracking"}
        </span>
      </div>

      {lat !== null && lng !== null ? (
        <MapView height="240px" markers={[{ id: "vehicle", lat, lng, color: "#2563eb", pulse: true, popupHtml: vehicleName || "Vehicle" }]} zoom={15} />
      ) : (
        <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-400">
          {isDriver ? "Tap “Share My Location” below to start live tracking for this trip." : "Waiting for the driver to start sharing their location..."}
        </p>
      )}

      <p className="mt-2 text-xs text-slate-400">Last updated: {timeAgo(updatedAt)}</p>

      {isDriver && (
        <div className="mt-3 space-y-2 border-t border-slate-100 pt-3">
          {geoError && (
            <p className="flex items-center gap-1.5 text-xs text-rose-600">
              <TriangleAlert size={13} /> {geoError}
            </p>
          )}
          <Button variant={sharing ? "danger" : "primary"} onClick={toggleSharing} className="w-full sm:w-auto">
            <Satellite size={15} />
            {sharing ? "Stop Sharing Location" : "Share My Location"}
          </Button>
          <p className="text-[11px] text-slate-400">Updates every 15 seconds while sharing is on. Turns off automatically once the trip is completed.</p>
        </div>
      )}
    </section>
  );
}
