// portal/frontend/app/dashboard/page.tsx
"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Me = { sub: string; name: string; email?: string | null; org_preferred?: string | null };
type Post = {
  id: string;
  lifecycle: "PUBLISHED" | "DRAFT";
  commentary: string;
  hashtags: string[];
  li_post_id?: string | null;
};

export default function DashboardPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [m, p] = await Promise.all([apiGet<Me>("/api/me"), apiGet<Post[]>("/api/posts")]);
        setMe(m);
        setPosts(p);
      } catch (e: any) {
        setErr(e.message || "Failed to load");
      }
    })();
  }, []);

  const runBatch = async () => {
    setLoading(true);
    setErr(null);
    try {
      await apiPost("/api/run-batch");
      alert("Batch run complete. Check the Approved page.");
    } catch (e: any) {
      setErr(e.message || "Batch failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold">Dashboard</h2>
          <p className="text-sm text-zinc-600">
            {me ? `Signed in as ${me.name}${me.org_preferred ? ` • Org: ${me.org_preferred}` : ""}` : "Not signed in"}
          </p>
        </div>

        <button
          onClick={runBatch}
          disabled={loading}
          className="inline-flex items-center rounded-lg bg-black px-4 py-2 text-white disabled:opacity-50"
        >
          {loading ? "Generating…" : "Generate Approved Posts"}
        </button>
      </div>

      {err && <div className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{err}</div>}

      <div className="grid gap-4">
        {posts.length === 0 ? (
          <div className="rounded-xl border border-zinc-200 bg-white p-6 text-zinc-600">
            No posts yet. Try running a batch or publish from the Approved queue.
          </div>
        ) : (
          posts.map((p) => (
            <div key={p.id} className="rounded-xl border border-zinc-200 bg-white p-4">
              <div className="mb-2 text-sm text-zinc-500">{p.lifecycle}</div>
              <div className="whitespace-pre-wrap">{p.commentary}</div>
              {p.hashtags?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {p.hashtags.map((h) => (
                    <span key={h} className="rounded-full bg-zinc-100 px-2 py-1 text-xs text-zinc-700">
                      #{h}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
