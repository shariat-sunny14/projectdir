"use server";

import { getSession } from "@/lib/auth/session";
import { searchLocations } from "@/lib/services/geocoding-service";
import type { GeoLocation } from "@/lib/types";

/** Powers the pickup/destination autocomplete input. Requires an authenticated
 * session (same access rule as the rest of the app) but no special role. */
export async function searchLocationsAction(query: string): Promise<GeoLocation[]> {
  const session = await getSession();
  if (!session) return [];
  return searchLocations(query);
}
