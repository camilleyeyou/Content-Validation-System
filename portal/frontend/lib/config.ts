// portal/frontend/lib/config.ts
// Centralized API helpers. Ensures cookies are sent cross-site so sessions work.

export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ||
    "https://content-validation-system-production.up.railway.app");

type ApiErrorShape = { detail?: string; message?: string; error?: string };

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const data = (await res.json()) as ApiErrorShape;
      msg = data.detail || data.message || data.error || msg;
    } catch {
      /* non-JSON body */
    }
    throw new Error(msg);
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;
  return undefined as T;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    credentials: "include", // ★ send cookies cross-site for session
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  return handle<T>(res);
}

export async function apiPost<T>(path: string, body?: any, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include", // ★ send cookies cross-site for session
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(init?.headers || {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...init,
  });
  return handle<T>(res);
}

export function linkedInLoginUrl(includeOrg = true, redirect?: string) {
  const url = new URL(`${API_BASE}/auth/linkedin/login`);
  if (includeOrg) url.searchParams.set("include_org", "true");
  if (redirect) url.searchParams.set("redirect", redirect);
  return url.toString();
}

/* =========================
   Approved queue helpers
   ========================= */

export type ApprovedRec = {
  id: string;
  content: string;
  hashtags: string[];
  status: string;
  created_at: string;
  li_post_id?: string | null;
  error_message?: string | null;
};

function coerceStringArray(x: any): string[] {
  if (Array.isArray(x)) return x.map((v) => String(v)).filter(Boolean);
  if (typeof x === "string" && x.length) return [x];
  return [];
}

function coerceApproved(item: any): ApprovedRec | null {
  if (!item) return null;
  const id = String(item.id || "");
  if (!id) return null;
  return {
    id,
    content: String(item.content ?? ""),
    hashtags: coerceStringArray(item.hashtags),
    status: String(item.status ?? "approved"),
    created_at: String(item.created_at ?? new Date().toISOString()),
    li_post_id: item.li_post_id ?? null,
    error_message: item.error_message ?? null,
  };
}

/**
 * Accepts any of the shapes the API might return and normalizes to ApprovedRec[].
 * Supports:
 *  - Array<ApprovedRecLike>
 *  - { items: Array }
 *  - { approved: Array }
 *  - { data: Array }
 */
export function normalizeApprovedResponse(raw: any): ApprovedRec[] {
  let arr: any[] = [];
  if (Array.isArray(raw)) arr = raw;
  else if (raw && Array.isArray(raw.items)) arr = raw.items;
  else if (raw && Array.isArray(raw.approved)) arr = raw.approved;
  else if (raw && Array.isArray(raw.data)) arr = raw.data;

  const mapped = arr
    .map(coerceApproved)
    .filter((x): x is ApprovedRec => !!x);

  // de-dupe by id just in case
  const seen = new Set<string>();
  const deduped: ApprovedRec[] = [];
  for (const p of mapped) {
    if (!seen.has(p.id)) {
      seen.add(p.id);
      deduped.push(p);
    }
  }
  return deduped;
}

/** Fetches approved posts and normalizes the shape. */
export async function fetchApproved(): Promise<ApprovedRec[]> {
  const raw = await apiGet<any>("/api/approved");
  return normalizeApprovedResponse(raw);
}
