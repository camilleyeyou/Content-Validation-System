// portal/frontend/app/approved/page.tsx
"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Approved = {
  id: string;
  content: string;
  hashtags: string[];
  status: string;
  error_message?: string | null;
};

export default function ApprovedPage() {
  const [rows, setRows] = useState<Approved[]>([]);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [published, setPublished] = useState<string[]>([]);

  const load = async () => {
    setErr(null);
    try {
      const data = await apiGet<Approved[]>("/api/approved");
      setRows(data);
    } catch (e: any) {
      setErr(e.message || "Failed to load approved posts");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const publishSelected = async () => {
    const ids = Object.entries(selected)
      .filter(([, v]) => v)
      .map(([k]) => k);
    if (ids.length === 0) return;

    setLoading(true);
    setErr(null);
    try {
      const res = await apiPost<{ successful: number; results: any[] }>(
        "/api/approved/publish",
        { ids, target: "AUTO", publish_now: true }
      );
      setPublished(ids);
      alert(`Published ${res.successful} posts.`);
      await load();
    } catch (e: any) {
      setErr(e.message || "Failed to publish");
    } finally {
      setLoading(false);
    }
  };

  const clearAll = async () => {
    setLoading(true);
    setErr(null);
    try {
      await apiPost("/api/approved/clear");
      setSelected({});
      await load();
    } catch (e: any) {
      setErr(e.message || "Failed to clear");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Approved queue</h2>
        <div className="flex items-center gap-2">
          <button
            onClick={publishSelected}
            disabled={loading}
            className="inline-flex items-center rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50"
          >
            {loading ? "Publishing…" : "Publish selected"}
          </button>
          <button
            onClick={clearAll}
            disabled={loading}
            className="inline-flex items-center rounded-lg border border-zinc-300 px-4 py-2 hover:bg-zinc-50 disabled:opacity-50"
          >
            Clear all
          </button>
        </div>
      </div>

      {err && <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{err}</div>}

      <div className="grid gap-4">
        {rows.length === 0 ? (
          <div className="rounded-xl border border-zinc-200 bg-white p-6 text-zinc-600">
            Nothing here yet. Run a batch from the Dashboard.
          </div>
        ) : (
          rows.map((r) => (
            <label
              key={r.id}
              className={`block rounded-xl border p-4 ${
                selected[r.id] ? "border-black bg-zinc-50" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="mb-2 flex items-center justify-between">
                <div className="text-sm text-zinc-500">{r.status}</div>
                <input
                  type="checkbox"
                  checked={!!selected[r.id]}
                  onChange={(e) =>
                    setSelected((prev) => ({ ...prev, [r.id]: e.target.checked }))
                  }
                />
              </div>

              <div className="whitespace-pre-wrap">{r.content}</div>

              {r.hashtags?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {r.hashtags.map((h) => (
                    <span key={h} className="rounded-full bg-zinc-100 px-2 py-1 text-xs text-zinc-700">
                      #{h}
                    </span>
                  ))}
                </div>
              )}

              {r.error_message && (
                <div className="mt-2 rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-900">
                  {r.error_message}
                </div>
              )}

              {published.includes(r.id) && (
                <div className="mt-2 rounded-md border border-emerald-300 bg-emerald-50 p-2 text-xs text-emerald-900">
                  Published
                </div>
              )}
            </label>
          ))
        )}
      </div>
    </div>
  );
}
