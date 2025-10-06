// portal/frontend/lib/config.ts

// Centralized API base & helpers so every component is consistent.

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8001")
  .replace(/\/+$/, "");

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
  return res.json() as Promise<T>;
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
  return res.json() as Promise<T>;
}

/**
 * Optional helper so TokenSync.tsx can compile even if it's not needed.
 * The backend sets a cookie session on /auth/linkedin/callback, so we don't
 * need to read tokens from the URL in the frontend. This is a no-op.
 */
export function syncTokenFromUrl(): boolean {
  return false;
}
