import { OAuth2Client } from "google-auth-library";

let client: OAuth2Client | null = null;

function getClient() {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  if (!clientId) throw new Error("Google sign-in is not configured on this server.");
  if (!client) client = new OAuth2Client(clientId);
  return client;
}

export interface GoogleProfile {
  email: string;
  name: string;
  picture?: string;
  googleId: string;
  emailVerified: boolean;
}

/** Verifies a Google Identity Services ID token server-side (signature, audience,
 * issuer, expiry) and returns the verified profile. Never trust a client-supplied
 * profile without this. */
export async function verifyGoogleIdToken(idToken: string): Promise<GoogleProfile> {
  const c = getClient();
  const ticket = await c.verifyIdToken({ idToken, audience: process.env.GOOGLE_CLIENT_ID });
  const payload = ticket.getPayload();
  if (!payload || !payload.email) {
    throw new Error("Could not verify Google account.");
  }
  return {
    email: payload.email,
    name: payload.name || payload.email,
    picture: payload.picture,
    googleId: payload.sub,
    emailVerified: !!payload.email_verified,
  };
}
