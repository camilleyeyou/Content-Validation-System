// portal/frontend/lib/config.ts
"use client";

export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001").replace(/\/+$/, "");

export const linkedInLoginUrl = (includeOrg = true) =>
  `${API_BASE}/auth/linkedin/login${includeOrg ? "?include_org=true" : ""}`;

const TOKEN_KEY = "portal_token";

export function getToken(): string | undefined {
  if (typeof window === "undefined") return undefined;
  return localStorage.getItem(TOKEN_KEY) || undefined;
}

export function setToken(token?: string) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function syncTokenFromUrl() {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  const t = url.searchParams.get("t");
  if (t) {
    setToken(t);
    url.searchParams.delete("t");
    window.history.replaceState({}, "", url.toString());
  }
}

function authHeaders() {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const t = getToken();
  if (t) headers["Authorization"] = `Bearer ${t}`;
  return headers;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: authHeaders(),
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
    headers: authHeaders(),
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
