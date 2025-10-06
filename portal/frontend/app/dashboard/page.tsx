"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "@/lib/api";

type Me = { sub: string; name: string; email?: string | null; org_preferred?: string | null };
type Org = { id: string; urn: string };
type Post = {
  id: string;
  lifecycle: "PUBLISHED" | "DRAFT";
  commentary: string;
  hashtags: string[];
  li_post_id?: string | null;
};

export default function DashboardPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const m = await apiGet<Me>("/api/me");
        setMe(m);
      } catch (e: any) {
        setErr(e.message || "Failed to load /api/me");
      }

      try {
        const o = await apiGet<{ orgs: Org[] }>("/api/orgs");
        setOrgs(o.orgs || []);
      } catch {
        // Some users won’t have org scopes; ignore here.
      }

      try {
        const p = await apiGet<Post[]>("/api/posts");
        setPosts(p);
      } catch (e: any) {
        setErr(e.message || "Failed to load /api/posts");
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
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

      {orgs.length > 0 && (
        <div className="rounded-xl border border-zinc-200 bg-white p-4">
          <div className="mb-2 text-sm font-medium">Organizations</div>
          <div className="flex flex-wrap gap-2">
            {orgs.map((o) => (
              <span key={o.id} className="rounded-full bg-zinc-100 px-3 py-1 text-xs text-zinc-700">
                {o.id} <span className="text-zinc-400">({o.urn})</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {err && <div className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-800">{err}</div>}

      <div className="rounded-xl border border-zinc-200 bg-white">
        <div className="border-b border-zinc-200 p-4 text-sm font-medium">Your Posts</div>
        <div className="divide-y divide-zinc-200">
          {posts.length === 0 ? (
            <div className="p-6 text-zinc-600">No posts yet. Try running a batch or publish from the Approved queue.</div>
          ) : (
            posts.map((p) => (
              <div key={p.id} className="p-4">
                <div className="mb-1 flex items-center justify-between text-sm text-zinc-500">
                  <span>{p.lifecycle}</span>
                  {p.li_post_id && <span className="text-zinc-400">LinkedIn ID: {p.li_post_id}</span>}
                </div>
                <div className="whitespace-pre-wrap break-words">{p.commentary}</div>
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
    </div>
  );
}
