"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { googleSignInAction, completeGoogleSignupAction } from "@/lib/actions/google-auth-actions";
import { Field, inputClass } from "@/components/ui/field";
import { Button } from "@/components/ui/button";
import type { Department } from "@/lib/types";

const GSI_SRC = "https://accounts.google.com/gsi/client";

/** Loads the Google Identity Services script exactly once per page and resolves
 * for every caller — including ones that mount after it already finished
 * loading (e.g. this component remounting after a client-side/soft navigation
 * such as logout, where the <script> tag from the previous mount is still in
 * the DOM but next/script's onLoad never fires again for the new instance). */
let gsiLoadPromise: Promise<void> | null = null;
function loadGoogleIdentityScript(): Promise<void> {
  if (typeof window !== "undefined" && window.google?.accounts?.id) return Promise.resolve();
  if (gsiLoadPromise) return gsiLoadPromise;

  gsiLoadPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${GSI_SRC}"]`);
    if (existing) {
      if (window.google?.accounts?.id) {
        resolve();
      } else {
        existing.addEventListener("load", () => resolve());
        existing.addEventListener("error", () => reject(new Error("Failed to load Google Sign-In script.")));
      }
      return;
    }

    const script = document.createElement("script");
    script.src = GSI_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Sign-In script."));
    document.head.appendChild(script);
  });

  return gsiLoadPromise;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: { client_id: string; callback: (resp: { credential: string }) => void }) => void;
          renderButton: (el: HTMLElement, options: Record<string, unknown>) => void;
        };
      };
    };
  }
}

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

export function GoogleSignInButton({ departments }: { departments: Department[] }) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [pendingIdToken, setPendingIdToken] = useState<string | null>(null);
  const [newProfile, setNewProfile] = useState<{ email: string; name: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!CLIENT_ID) return;
    let cancelled = false;
    loadGoogleIdentityScript()
      .then(() => {
        if (!cancelled) setScriptLoaded(true);
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load Google Sign-In. Check your connection and try again.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!scriptLoaded || !CLIENT_ID || !buttonRef.current || !window.google) return;

    window.google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: async (resp) => {
        setError(null);
        setInfo(null);
        const result = await googleSignInAction(resp.credential);
        if (!result.ok) {
          setError(result.error.message);
          return;
        }
        const data = result.data;
        if (data.status === "signed_in") {
          router.push("/dashboard");
          router.refresh();
        } else if (data.status === "needs_profile") {
          setPendingIdToken(resp.credential);
          setNewProfile({ email: data.email!, name: data.name! });
        } else {
          setInfo(data.message || null);
        }
      },
    });
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: "outline",
      size: "large",
      width: 336,
      text: "continue_with",
    });
  }, [scriptLoaded, router]);

  if (!CLIENT_ID) {
    return (
      <Button type="button" variant="secondary" className="w-full" disabled title="Set NEXT_PUBLIC_GOOGLE_CLIENT_ID to enable">
        Continue with Google
      </Button>
    );
  }

  if (newProfile && pendingIdToken) {
    return (
      <form action={completeGoogleSignupAction} className="space-y-3 rounded-xl border border-slate-200 p-4">
        <input type="hidden" name="idToken" value={pendingIdToken} />
        <p className="text-sm text-slate-600">
          Welcome, <strong>{newProfile.name}</strong>! A few more details to finish signing up with{" "}
          <span className="text-slate-500">{newProfile.email}</span>:
        </p>
        <Field label="Phone" required>
          <input name="phone" required className={inputClass} />
        </Field>
        <Field label="Department" required>
          <select name="departmentId" required className={inputClass} defaultValue="">
            <option value="" disabled>
              Select department
            </option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Designation" required>
          <input name="designation" required className={inputClass} />
        </Field>
        <Button type="submit" className="w-full">
          Complete sign up
        </Button>
      </form>
    );
  }

  return (
    <>
      {error && <div className="mb-2 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      {info && <div className="mb-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-700">{info}</div>}
      <div ref={buttonRef} className="flex justify-center" />
    </>
  );
}
