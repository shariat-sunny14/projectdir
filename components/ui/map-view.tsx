"use client";

import { useEffect, useRef } from "react";
import type { Map as LeafletMap, LayerGroup } from "leaflet";
import "leaflet/dist/leaflet.css";

export interface MapMarker {
  id: string;
  lat: number;
  lng: number;
  color?: string; // any CSS color
  label?: string; // short letter/icon shown inside the pin
  popupHtml?: string;
  pulse?: boolean; // animated "live" ring, used for moving vehicles
}

export interface MapViewProps {
  markers: MapMarker[];
  path?: { lat: number; lng: number }[];
  height?: string;
  className?: string;
  zoom?: number;
  interactive?: boolean;
}

const DEFAULT_CENTER: [number, number] = [23.8103, 90.4125]; // Dhaka — sensible fallback when there's nothing to show yet

function renderLayers(
  L: typeof import("leaflet"),
  map: LeafletMap,
  layer: LayerGroup,
  markers: MapMarker[],
  path: { lat: number; lng: number }[] | undefined,
  zoom: number | undefined
) {
  layer.clearLayers();
  const points: [number, number][] = [];

  if (path && path.length > 1) {
    const line = L.polyline(
      path.map((p) => [p.lat, p.lng]),
      { color: "#6366f1", weight: 4, opacity: 0.7, dashArray: "1 8", lineCap: "round" }
    );
    layer.addLayer(line);
  }

  for (const m of markers) {
    const marker = L.marker([m.lat, m.lng], { icon: pinIcon(L, m.color || "#4f46e5", m.label, m.pulse) });
    if (m.popupHtml) marker.bindPopup(m.popupHtml);
    layer.addLayer(marker);
    points.push([m.lat, m.lng]);
  }

  if (points.length === 1) {
    map.setView(points[0], zoom ?? 14);
  } else if (points.length > 1) {
    map.fitBounds(L.latLngBounds(points), { padding: [32, 32], maxZoom: 15 });
  }
}

function pinIcon(L: typeof import("leaflet"), color: string, label?: string, pulse?: boolean) {
  return L.divIcon({
    className: "",
    html: `
      <div style="position:relative;width:30px;height:38px;">
        ${pulse ? `<span style="position:absolute;left:3px;top:3px;width:24px;height:24px;border-radius:9999px;background:${color};opacity:0.35;animation:map-pulse 1.6s ease-out infinite;"></span>` : ""}
        <svg width="30" height="38" viewBox="0 0 30 38" xmlns="http://www.w3.org/2000/svg" style="position:relative;filter:drop-shadow(0 2px 3px rgba(0,0,0,0.35));">
          <path d="M15 0C6.7 0 0 6.7 0 15c0 10.5 15 23 15 23s15-12.5 15-23C30 6.7 23.3 0 15 0z" fill="${color}"/>
          <circle cx="15" cy="15" r="7" fill="white"/>
        </svg>
        ${label ? `<span style="position:absolute;left:0;top:5px;width:30px;text-align:center;font-size:10px;font-weight:700;color:${color};">${label}</span>` : ""}
      </div>
    `,
    iconSize: [30, 38],
    iconAnchor: [15, 36],
    popupAnchor: [0, -34],
  });
}

/** Vanilla Leaflet map (no react-leaflet) with divIcon pins — used for the
 * pickup/destination preview, the booking detail route card, and the live
 * fleet tracking views. Leaflet is imported dynamically inside an effect so
 * it never touches `window` during server rendering. */
export function MapView({ markers, path, height = "260px", className = "", zoom, interactive = true }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<LeafletMap | null>(null);
  const layerRef = useRef<LayerGroup | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !containerRef.current || mapRef.current) return;

      const map = L.map(containerRef.current, {
        zoomControl: interactive,
        dragging: interactive,
        scrollWheelZoom: false,
        doubleClickZoom: interactive,
        touchZoom: interactive,
        boxZoom: false,
        keyboard: false,
      }).setView(DEFAULT_CENTER, zoom ?? 12);

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      mapRef.current = map;
      layerRef.current = L.layerGroup().addTo(map);
      renderLayers(L, map, layerRef.current, markers, path, zoom);
    })();

    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      layerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    (async () => {
      const L = (await import("leaflet")).default;
      const map = mapRef.current;
      const layer = layerRef.current;
      if (!map || !layer) return;
      renderLayers(L, map, layer, markers, path, zoom);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(markers), JSON.stringify(path)]);

  return (
    <div className={`overflow-hidden rounded-xl border border-slate-200 ${className}`}>
      <div ref={containerRef} style={{ height, width: "100%" }} />
      <style jsx global>{`
        @keyframes map-pulse {
          0% {
            transform: scale(0.6);
            opacity: 0.5;
          }
          100% {
            transform: scale(1.8);
            opacity: 0;
          }
        }
        .leaflet-popup-content-wrapper {
          border-radius: 10px;
        }
      `}</style>
    </div>
  );
}
