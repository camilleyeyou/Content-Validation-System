// portal/frontend/app/page.tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8001";

type PostRow = {
  id: string;
  target_type: "MEMBER" | "ORG";
  lifecycle: string;
  commentary?: string;
  content?: string;
  hashtags?: string[];
  // Image fields (NEW)
  image_url?: string;
  image_description?: string;
  image_prompt?: string;
  image_revised_prompt?: string;
  has_image?: boolean;
  // Status fields
  li_post_id?: string;
  error_message?: string;
  created_at?: string;
};

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);
  const [rows, setRows] = useState<PostRow[]>([]);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  async function fetchJSON(url: string, opts: any = {}) {
    const r = await fetch(url, { ...opts });
    const text = await r.text();
    if (!r.ok) throw new Error(text || `${r.status} ${r.statusText}`);
    try {
      return JSON.parse(text);
    } catch {
      return text;
    }
  }

  async function loadMe() {
    try {
      setMe(await fetchJSON(`${API_BASE}/api/me`));
    } catch {}
  }

  async function loadPosts() {
    try {
      setRows(await fetchJSON(`${API_BASE}/api/approved`));
    } catch {}
  }

  useEffect(() => {
    loadMe();
    loadPosts();
  }, []);

  async function runBatch() {
    setMsg("Running content generation with DALL-E images...");
    setLoading(true);
    try {
      const data = await fetchJSON(`${API_BASE}/api/run-batch`, { method: "POST" });
      const imageInfo = data.posts_with_images > 0 
        ? ` (${data.posts_with_images} with images)` 
        : "";
      setMsg(
        `✅ Generated ${data.approved_count || 0} approved posts${imageInfo}! Total in queue: ${
          data.total_in_queue || 0
        }`
      );
      await loadPosts();
    } catch (e: any) {
      setMsg(`❌ Error: ${e?.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }

  async function clearAll() {
    if (!confirm("Clear all posts from queue?")) return;
    setMsg("");
    setLoading(true);
    try {
      const data = await fetchJSON(`${API_BASE}/api/approved/clear`, { method: "POST" });
      setMsg(`✅ Cleared ${data.deleted} posts`);
      await loadPosts();
    } catch (e: any) {
      setMsg(`❌ Error: ${e?.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }

  // Count posts with images
  const postsWithImages = rows.filter(r => r.has_image).length;

  return (
    <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Content Dashboard</h1>
        <p className="text-sm text-zinc-600">
          {me ? (
            <>
              Acting as <span className="font-semibold">{me.name || me.sub}</span>
            </>
          ) : (
            "Loading..."
          )}
        </p>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border border-zinc-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={runBatch}
            disabled={loading}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
          >
            {loading ? (
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              "🚀"
            )}
            Generate Posts + Images
          </button>
          <button
            onClick={clearAll}
            disabled={loading}
            className="px-6 py-3 bg-white border border-zinc-300 rounded-lg font-semibold hover:bg-zinc-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            🗑️ Clear Queue
          </button>
          <Link
            href="/prompts"
            className="px-6 py-3 bg-zinc-900 text-white rounded-lg font-semibold hover:bg-zinc-800 transition-all inline-flex items-center gap-2"
          >
            🤖 Manage Agent Prompts
          </Link>
        </div>

        {msg && (
          <div
            className={`mt-4 p-4 rounded-lg text-sm ${
              msg.includes("❌")
                ? "bg-red-50 text-red-800 border border-red-200"
                : "bg-green-50 text-green-800 border border-green-200"
            }`}
          >
            {msg}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="bg-white rounded-xl border border-zinc-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">Statistics</h2>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-6">
          <div>
            <div className="text-xs text-zinc-600 mb-1">Total Posts</div>
            <div className="text-3xl font-bold">{rows.length}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-600 mb-1">With Images</div>
            <div className="text-3xl font-bold text-blue-600">{postsWithImages}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-600 mb-1">Image Rate</div>
            <div className="text-lg font-semibold">
              {rows.length > 0 ? `${Math.round((postsWithImages / rows.length) * 100)}%` : "0%"}
            </div>
          </div>
          <div>
            <div className="text-xs text-zinc-600 mb-1">Status</div>
            <div className={`text-lg font-semibold ${rows.length > 0 ? "text-green-600" : "text-zinc-500"}`}>
              {rows.length > 0 ? "Ready to Publish" : "No Posts"}
            </div>
          </div>
        </div>
      </div>

      {/* Posts List */}
      <div className="bg-white rounded-xl border border-zinc-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">Generated Posts ({rows.length})</h2>
        <div className="space-y-4">
          {rows.length === 0 ? (
            <div className="text-center py-12 text-zinc-500 text-sm">
              No posts yet. Click "Generate Posts + Images" to create content using your AI agents.
            </div>
          ) : (
            rows.map((r) => {
              const displayContent = r.content || r.commentary || "";
              const full =
                displayContent +
                (r.hashtags?.length ? "\n\n" + r.hashtags.map((h) => `#${h}`).join(" ") : "");
              return (
                <div
                  key={r.id}
                  className="border border-zinc-200 rounded-lg p-4 bg-zinc-50 hover:shadow-md transition-shadow"
                >
                  {/* Header with tags */}
                  <div className="flex gap-2 flex-wrap mb-3 text-xs">
                    <span className="px-2 py-1 bg-blue-600 text-white rounded-full font-semibold">
                      {r.target_type}
                    </span>
                    <span className="px-2 py-1 bg-zinc-200 text-zinc-700 rounded-full font-medium">
                      {r.lifecycle}
                    </span>
                    {r.has_image && (
                      <span className="px-2 py-1 bg-purple-600 text-white rounded-full font-semibold">
                        🖼️ Image
                      </span>
                    )}
                    {r.created_at && (
                      <span className="ml-auto text-zinc-500">
                        {new Date(r.created_at).toLocaleString()}
                      </span>
                    )}
                  </div>

                  {/* Image Display (NEW) */}
                  {r.image_url && (
                    <div className="mb-4 rounded-lg overflow-hidden border border-zinc-200">
                      <img
                        src={r.image_url}
                        alt={r.image_description || "Generated image"}
                        className="w-full h-auto"
                        loading="lazy"
                      />
                      {r.image_description && (
                        <div className="p-3 bg-zinc-100 text-xs text-zinc-700">
                          <span className="font-semibold">Image: </span>
                          {r.image_description}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Content */}
                  <div className="whitespace-pre-wrap mb-3 leading-relaxed text-sm">
                    {displayContent}
                  </div>

                  {/* Hashtags */}
                  {r.hashtags?.length ? (
                    <div className="mb-3 flex gap-2 flex-wrap">
                      {r.hashtags.map((h, i) => (
                        <span
                          key={i}
                          className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full font-medium"
                        >
                          #{h}
                        </span>
                      ))}
                    </div>
                  ) : null}

                  {/* Status Messages */}
                  {r.li_post_id && (
                    <div className="text-xs text-green-700 font-medium mb-2">
                      ✅ Published • LinkedIn ID: {r.li_post_id}
                    </div>
                  )}
                  {r.error_message && (
                    <div className="text-xs text-red-700 bg-red-50 p-2 rounded mb-2">
                      ❌ Error: {r.error_message}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => navigator.clipboard.writeText(displayContent)}
                      className="px-3 py-2 text-xs border border-zinc-300 rounded-lg hover:bg-zinc-100 transition-colors"
                    >
                      📋 Copy Text
                    </button>
                    <button
                      onClick={() => navigator.clipboard.writeText(full)}
                      className="px-3 py-2 text-xs border border-zinc-300 rounded-lg hover:bg-zinc-100 transition-colors"
                    >
                      📋 Copy with Tags
                    </button>
                    {r.image_url && (
                      <>
                        <button
                          onClick={() => window.open(r.image_url, '_blank')}
                          className="px-3 py-2 text-xs border border-zinc-300 rounded-lg hover:bg-zinc-100 transition-colors"
                        >
                          🖼️ Open Image
                        </button>
                        {r.image_prompt && (
                          <button
                            onClick={() => {
                              const info = `Image Prompt: ${r.image_prompt}\n\nImage Description: ${r.image_description || 'N/A'}`;
                              alert(info);
                            }}
                            className="px-3 py-2 text-xs border border-zinc-300 rounded-lg hover:bg-zinc-100 transition-colors"
                          >
                            ℹ️ Image Details
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </main>
  );
}