import type { ReactNode } from "react";
import { MapPin, Navigation } from "lucide-react";
import { MapView } from "@/components/ui/map-view";
import type { GeoLocation } from "@/lib/types";

/** Feature #6 (steps 7-8): shows the selected pickup/destination location details
 * and plots both pins on a map on the booking details page. Falls back to a
 * text-only view for legacy bookings created before coordinates were captured. */
export function RouteMapCard({
  pickup,
  destination,
  pickupLabel,
  destinationLabel,
}: {
  pickup?: GeoLocation;
  destination?: GeoLocation;
  pickupLabel: string;
  destinationLabel: string;
}) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm shadow-slate-200/50">
      <h2 className="mb-3 font-semibold text-slate-900">Route</h2>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="space-y-3">
          <LocationRow icon={<MapPin size={15} className="text-emerald-600" />} label="Pickup" loc={pickup} fallback={pickupLabel} />
          <LocationRow icon={<Navigation size={15} className="text-rose-600" />} label="Destination" loc={destination} fallback={destinationLabel} />
        </div>
        {pickup && destination ? (
          <MapView
            height="200px"
            markers={[
              { id: "pickup", lat: pickup.lat, lng: pickup.lng, color: "#059669", label: "A", popupHtml: `<strong>Pickup</strong><br/>${pickup.name}` },
              { id: "dest", lat: destination.lat, lng: destination.lng, color: "#e11d48", label: "B", popupHtml: `<strong>Destination</strong><br/>${destination.name}` },
            ]}
            path={[pickup, destination]}
          />
        ) : (
          <div className="flex items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-400">
            Map coordinates aren&apos;t available for this booking (created before location search was added).
          </div>
        )}
      </div>
    </section>
  );
}

function LocationRow({ icon, label, loc, fallback }: { icon: ReactNode; label: string; loc?: GeoLocation; fallback: string }) {
  return (
    <div className="flex items-start gap-2.5">
      <div className="mt-0.5">{icon}</div>
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
        <p className="text-sm font-medium text-slate-800">{loc?.name || fallback}</p>
        {loc?.address && <p className="text-xs text-slate-500">{loc.address}</p>}
        {loc && <p className="text-[11px] text-slate-400">{loc.lat.toFixed(5)}, {loc.lng.toFixed(5)}</p>}
      </div>
    </div>
  );
}
