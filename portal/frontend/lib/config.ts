"use client";

// ---- API Base & helpers ----
export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8080").replace(
  /\/+$/,
  ""
);

export function linkedInLoginUrl(includeOrg = true, redirect?: string) {
  const qs = new URLSearchParams();
  if (includeOrg) qs.set("include_org", "true");
  if (redirect) qs.set("redirect", redirect);
  return `${API_BASE}/auth/linkedin/login${qs.toString() ? `?${qs.toString()}` : ""}`;
}

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

// ---- Types used around the app ----
export type ApprovedRec = {
  id: string;
  content: string;
  hashtags: string[];
  status: string;
  created_at: string;
  li_post_id?: string | null;
  error_message?: string | null;
  user_sub?: string;
};

// ---- Normalizers to tolerate both old and new API shapes ----
export function normalizeApprovedResponse(raw: any): ApprovedRec[] {
  if (Array.isArray(raw)) return raw as ApprovedRec[];
  if (raw && Array.isArray(raw.items)) return raw.items as ApprovedRec[];
  // Some callers may pass {data: [...]} etc; be forgiving:
  if (raw?.data && Array.isArray(raw.data)) return raw.data as ApprovedRec[];
  return [];
}

// Convenience wrappers
export async function fetchApproved(): Promise<ApprovedRec[]> {
  const raw = await apiGet<any>("/api/approved");
  return normalizeApprovedResponse(raw);
}

export async function runBatch(count = 3): Promise<ApprovedRec[]> {
  // Backend reads 'count' from query in our latest main, but sending in body is harmless.
  const raw = await apiPost<any>("/api/run-batch", { count });
  // Return newly created items (if present) so UI can append immediately.
  return normalizeApprovedResponse(raw);
}
