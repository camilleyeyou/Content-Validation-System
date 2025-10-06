// portal/frontend/lib/config.ts
"use client";

// Build the API base once
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001").replace(
  /\/+$/,
  ""
);

// Capture ?t=... on first load and stash it for future API calls
(function captureToken() {
  try {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    const t = url.searchParams.get("t");
    if (t) {
      localStorage.setItem("portal_token", t);
      url.searchParams.delete("t");
      // Clean the URL without losing history
      window.history.replaceState({}, "", url.toString());
    }
  } catch {}
})();

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem("portal_token");
  } catch {
    return null;
  }
}

export const linkedInLoginUrl = (includeOrg = true) =>
  `${API_BASE}/auth/linkedin/login${includeOrg ? "?include_org=true" : ""}`;

// Shared fetch helpers
async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    credentials: "include", // allows cookie if the browser permits it
    cache: "no-store",
    mode: "cors",
  });
  if (!res.ok) {
    const txt = await res.text().catch(() => "");
    throw new Error(txt || `${init?.method || "GET"} ${path} failed: ${res.status}`);
  }
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

export function apiGet<T>(path: string) {
  return fetchJSON<T>(path);
}

export function apiPost<T>(path: string, body?: unknown) {
  return fetchJSON<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}
