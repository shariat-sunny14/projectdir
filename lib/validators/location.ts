import { z } from "zod";

export const geoLocationSchema = z.object({
  name: z.string().min(1),
  address: z.string().min(1),
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
});

/** Parses the JSON blob a form field carries for a selected map location.
 * Returns undefined (rather than throwing) when the field is missing/malformed,
 * so callers can decide how strictly to require it. */
export function parseGeoLocationField(raw: FormDataEntryValue | null): z.infer<typeof geoLocationSchema> | undefined {
  if (!raw || typeof raw !== "string") return undefined;
  try {
    const parsed = geoLocationSchema.safeParse(JSON.parse(raw));
    return parsed.success ? parsed.data : undefined;
  } catch {
    return undefined;
  }
}
