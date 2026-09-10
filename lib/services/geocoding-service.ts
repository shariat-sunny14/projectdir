import type { GeoLocation } from "@/lib/types";

/**
 * Free, keyless geocoding via OpenStreetMap Nominatim — powers the Uber-style
 * pickup/destination autocomplete (Feature #6) without requiring a paid Maps API key.
 * Nominatim's usage policy requires a descriptive User-Agent and no more than ~1 req/s,
 * which the caller's debounce naturally respects.
 */
export async function searchLocations(query: string): Promise<GeoLocation[]> {
  const q = query.trim();
  if (q.length < 3) return [];

  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.searchParams.set("q", q);
  url.searchParams.set("format", "jsonv2");
  url.searchParams.set("addressdetails", "1");
  url.searchParams.set("limit", "6");

  try {
    const res = await fetch(url.toString(), {
      headers: {
        "User-Agent": "FactoryFleetManagement/1.0 (internal fleet booking tool)",
        "Accept-Language": "en",
      },
      signal: AbortSignal.timeout(6000),
    });
    if (!res.ok) return [];

    const results = (await res.json()) as Array<{
      display_name: string;
      lat: string;
      lon: string;
      name?: string;
      address?: Record<string, string>;
    }>;

    return results.map((r) => {
      const parts = r.display_name.split(",").map((p) => p.trim());
      const name = r.name || parts[0] || r.display_name;
      const address = r.display_name;
      return {
        name,
        address,
        lat: Number(r.lat),
        lng: Number(r.lon),
      };
    });
  } catch {
    // Network hiccup or Nominatim rate-limit — fail soft, the UI falls back to free typing.
    return [];
  }
}

/** Reverse geocode a lat/lng into a human label — used when a driver's live pin needs a place name. */
export async function reverseGeocode(lat: number, lng: number): Promise<string | null> {
  const url = new URL("https://nominatim.openstreetmap.org/reverse");
  url.searchParams.set("lat", String(lat));
  url.searchParams.set("lon", String(lng));
  url.searchParams.set("format", "jsonv2");

  try {
    const res = await fetch(url.toString(), {
      headers: { "User-Agent": "FactoryFleetManagement/1.0 (internal fleet booking tool)" },
      signal: AbortSignal.timeout(6000),
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { display_name?: string };
    return data.display_name ?? null;
  } catch {
    return null;
  }
}
