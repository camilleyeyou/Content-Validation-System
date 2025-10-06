// portal/frontend/lib/api.ts
"use client";

import { API_BASE } from "./config";

export const linkedInLoginUrl = (includeOrg = true) =>
  `${API_BASE}/auth/linkedin/login${includeOrg ? "?include_org=true" : ""}`;

async function handle<T>(res: Response, path: string, method: string): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `${method} ${path} failed: ${res.status}`);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  // allow non-JSON responses when needed
  return (await res.text()) as unknown as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
  });
  return handle<T>(res, path, "GET");
}

export async function apiPost<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  return handle<T>(res, path, "POST");
}
