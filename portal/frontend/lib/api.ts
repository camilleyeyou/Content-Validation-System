const API_BASE = process.env.NEXT_PUBLIC_PORTAL_API_BASE ?? "http://localhost:8001";

export async function api<T = any>(
  path: string,
  init?: RequestInit & { parseAs?: "json" | "text" }
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: init?.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    body: init?.body,
    credentials: "include", // IMPORTANT for Railway cookie
    cache: "no-store",
  });

  const parseAs = init?.parseAs ?? "json";
  if (!res.ok) {
    const txt = await res.text().catch(() => String(res.status));
    throw new Error(txt || `HTTP ${res.status}`);
  }
  // @ts-ignore
  return parseAs === "json" ? res.json() : res.text();
}
