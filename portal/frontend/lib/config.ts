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
      // non-JSON error; keep default msg
    }
    throw new Error(msg);
  }

  // tolerate empty response bodies
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return (await res.json()) as T;
  }
  return undefined as unknown as T;
}

export async function apiGet<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    credentials: "include",            // ★ send cookies cross-site
    headers: {
      Accept: "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  return handle<T>(res);
}

export async function apiPost<T>(
  path: string,
  body?: any,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",            // ★ send cookies cross-site
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
