import { cookies } from "next/headers";
import crypto from "crypto";
import type { Role } from "@/lib/types";

const SESSION_COOKIE = "fleet_session";
const SECRET = process.env.SESSION_SECRET || "dev-secret-change-me";

export interface SessionPayload {
  userId: string;
  role: Role;
  fullName: string;
  email: string;
}

function sign(data: string): string {
  return crypto.createHmac("sha256", SECRET).update(data).digest("hex");
}

export function encodeSession(payload: SessionPayload, remember: boolean): { value: string; maxAge: number } {
  const json = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const sig = sign(json);
  const maxAge = remember ? 60 * 60 * 24 * 30 : 60 * 60 * 8; // 30 days vs 8 hours
  return { value: `${json}.${sig}`, maxAge };
}

function decodeSession(token: string): SessionPayload | null {
  const [json, sig] = token.split(".");
  if (!json || !sig) return null;
  if (sign(json) !== sig) return null;
  try {
    return JSON.parse(Buffer.from(json, "base64url").toString("utf-8"));
  } catch {
    return null;
  }
}

export async function createSession(payload: SessionPayload, remember = false) {
  const { value, maxAge } = encodeSession(payload, remember);
  const store = await cookies();
  store.set(SESSION_COOKIE, value, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge,
  });
}

export async function getSession(): Promise<SessionPayload | null> {
  const store = await cookies();
  const token = store.get(SESSION_COOKIE)?.value;
  if (!token) return null;
  return decodeSession(token);
}

export async function destroySession() {
  const store = await cookies();
  store.delete(SESSION_COOKIE);
}
