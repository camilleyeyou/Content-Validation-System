// portal/frontend/lib/config.ts
"use client";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001").replace(/\/+$/, "");

export const linkedInLoginUrl = (includeOrg = true) =>
  `${API_BASE}/auth/linkedin/login${includeOrg ? "?include_org=true" : ""}`;

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    mode: "cors",
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(txt || `GET ${path} failed: ${res.status}`);
  }
  return res.json();
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
    mode: "cors",
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(txt || `POST ${path} failed: ${res.status}`);
  }
  return res.json();
}

/**
 * syncTokenFromUrl
 *  - We don't need URL tokens (session is cookie-based).
 *  - If a provider ever sends query params like ?access_token=... or ?sid=...
 *    this will just clean them from the URL bar so they don’t linger.
 *  - Returns true if any cleanup happened.
 */
export function syncTokenFromUrl(): boolean {
  if (typeof window === "undefined") return false;

  const url = new URL(window.location.href);
  const qp = url.searchParams;

  // anything you want to clean up, add here:
  const keys = ["access_token", "id_token", "token_type", "expires_in", "sid"];
  const hadAny = keys.some((k) => qp.has(k));

  if (!hadAny) return false;

  keys.forEach((k) => qp.delete(k));
  const newUrl = url.pathname + (qp.toString() ? `?${qp.toString()}` : "") + url.hash;
  window.history.replaceState({}, "", newUrl);

  return true;
}
