// portal/frontend/lib/config.ts
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ||
  "https://content-validation-system-production.up.railway.app";

async function handle<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`${r.status} ${txt || r.statusText}`);
  }
  return (await r.json()) as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    credentials: "omit",
  });
  return handle<T>(res);
}

export async function apiPost<T>(path: string, body: any): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body ?? {}),
    credentials: "omit",
  });
  return handle<T>(res);
}

export type ApprovedRec = {
  id: string;
  content: string;
  hashtags: string[];
  status: string;
  created_at: string;
  li_post_id?: string | null;
  error_message?: string | null;
};

export async function fetchApproved(): Promise<ApprovedRec[]> {
  try {
    const list = await apiGet<ApprovedRec[] | any>(`/api/approved`);
    return Array.isArray(list) ? list : [];
  } catch {
    return [];
  }
}
