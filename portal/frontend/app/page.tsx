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
  media_type?: "text" | "image" | "video";
  image_url?: string;
  image_description?: string;
  image_prompt?: string;
  image_revised_prompt?: string;
  has_image?: boolean;
  video_url?: string;
  video_description?: string;
  video_prompt?: string;
  video_generation_time?: number;
  video_size_mb?: number;
  has_video?: boolean;
  media_provider?: string;
  media_cost?: number;
  li_post_id?: string;
  error_message?: string;
  created_at?: string;
};

/** Normalize any media URL to the public images route on the API origin. */
function resolveMediaUrl(raw?: string): string | undefined {
  if (!raw) return undefined;
  if (/^https?:\/\//i.test(raw)) return raw;
  if (raw.startsWith("/images/")) return `${API_BASE}${raw}`;
  const parts = raw.split("/");
  const filename = parts[parts.length - 1] || raw;
  return `${API_BASE}/images/${filename}`;
}

async function fetchJSON(url: string, opts: RequestInit = {}) {
  const r = await fetch(url, { ...opts });
  const text = await r.text();
  if (!r.ok) throw new Error(text || `${r.status} ${r.statusText}`);
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export default function Dashboard() {
  const [me, setMe] = useState<any>(null);
  const [rows, setRows] = useState<PostRow[]>([]);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);
  const [showWorkflowGuide, setShowWorkflowGuide] = useState(false);

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
    setMsg("🔄 Running AI-powered content generation pipeline...");
    setLoading(true);
    try {
      const data = await fetchJSON(`${API_BASE}/api/run-batch`, { method: "POST" });
      const mediaInfo =
        data.posts_with_videos > 0
          ? ` (${data.posts_with_videos} with AI-generated videos)`
          : data.posts_with_images > 0
          ? ` (${data.posts_with_images} with AI-generated images)`
          : "";
      setMsg(
        `✅ Successfully generated ${data.approved_count || 0} approved posts${mediaInfo}! Total in queue: ${
          data.total_in_queue || 0
        }`
      );
      await loadPosts();
    } catch (e: any) {
      setMsg(`❌ Generation Error: ${e?.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }

  async function clearAll() {
    if (!confirm("⚠️ This will permanently delete all posts from the queue. Continue?")) return;
    setMsg("");
    setLoading(true);
    try {
      const data = await fetchJSON(`${API_BASE}/api/approved/clear`, { method: "POST" });
      setMsg(`✅ Successfully cleared ${data.deleted} posts from the queue`);
      await loadPosts();
    } catch (e: any) {
      setMsg(`❌ Clear Error: ${e?.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }

  // Count posts with media
  const postsWithVideos = rows.filter((r) => r.has_video || r.video_url).length;
  const postsWithImages = rows.filter((r) => r.has_image || (r.image_url && !r.video_url)).length;
  const postsWithMedia = postsWithVideos + postsWithImages;

  return (
    <main className="min-h-screen bg-gradient-to-br from-zinc-50 via-blue-50/30 to-zinc-50">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Enhanced Header with Workflow Context */}
        <div className="bg-white rounded-2xl border border-zinc-200 p-8 shadow-sm">
          <div className="flex items-start justify-between gap-6 mb-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                  AI
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-zinc-900">AI Content Generation Portal</h1>
                  <p className="text-sm text-zinc-600 mt-1">
                    Multi-Agent LinkedIn Content Creation & Management System
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-sm text-zinc-600 mt-4">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-lg border border-blue-100">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                  <span>
                    Acting as{" "}
                    <span className="font-semibold text-blue-900">{me?.name || me?.sub || "Loading..."}</span>
                  </span>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowWorkflowGuide(!showWorkflowGuide)}
              className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-all flex items-center gap-2"
            >
              <span className="text-lg">📖</span>
              {showWorkflowGuide ? "Hide" : "Show"} Workflow Guide
            </button>
          </div>

          {/* Workflow Guide */}
          {showWorkflowGuide && (
            <div className="bg-gradient-to-br from-blue-50 to-zinc-50 rounded-xl p-6 border border-blue-200">
              <h3 className="text-lg font-bold text-zinc-900 mb-4 flex items-center gap-2">
                <span className="text-2xl">🔄</span>
                How This AI Content System Works
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        1
                      </div>
                      <div>
                        <h4 className="font-semibold text-zinc-900 mb-1">Multi-Agent Generation</h4>
                        <p className="text-sm text-zinc-600">
                          Multiple specialized AI agents analyze your requirements and generate targeted LinkedIn
                          content for different audiences (Members vs Organizations) and lifecycle stages
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        2
                      </div>
                      <div>
                        <h4 className="font-semibold text-zinc-900 mb-1">AI Media Generation</h4>
                        <p className="text-sm text-zinc-600">
                          Each post can include AI-generated images or videos that are contextually relevant to the
                          content, enhancing engagement and visual appeal
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        3
                      </div>
                      <div>
                        <h4 className="font-semibold text-zinc-900 mb-1">Quality Validation</h4>
                        <p className="text-sm text-zinc-600">
                          Content passes through validation agents that ensure quality, tone, compliance, and brand
                          alignment before being approved for the queue
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        4
                      </div>
                      <div>
                        <h4 className="font-semibold text-zinc-900 mb-1">Customizable Prompts</h4>
                        <p className="text-sm text-zinc-600">
                          Fine-tune agent behavior and output style by customizing system and user prompts without
                          changing any code - perfect for testing different strategies
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-sm flex-shrink-0">
                        5
                      </div>
                      <div>
                        <h4 className="font-semibold text-zinc-900 mb-1">Review & Publish</h4>
                        <p className="text-sm text-zinc-600">
                          Review generated content with full media preview, copy to clipboard, and manage your content
                          queue before publishing to LinkedIn
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg p-4 border border-amber-200">
                    <div className="flex items-start gap-2">
                      <span className="text-xl">💡</span>
                      <div>
                        <h4 className="font-semibold text-amber-900 mb-1 text-sm">Pro Tip</h4>
                        <p className="text-xs text-amber-800">
                          Use the Agent Prompts Manager to test different content strategies and refine your AI's
                          output quality without touching the codebase
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions with Enhanced Descriptions */}
        <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-bold text-zinc-900">Content Generation Controls</h2>
              <p className="text-sm text-zinc-600 mt-1">Trigger AI workflows and manage your content pipeline</p>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3 mb-6">
            <button
              onClick={runBatch}
              disabled={loading}
              className="group relative overflow-hidden px-6 py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold hover:from-blue-700 hover:to-blue-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
            >
              <div className="flex items-center justify-center gap-3">
                {loading ? (
                  <span className="inline-block w-5 h-5 border-3 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <span className="text-2xl">✨</span>
                )}
                <div className="text-left">
                  <div className="font-bold">Generate Content</div>
                  <div className="text-xs text-blue-100 font-normal">Run AI multi-agent pipeline</div>
                </div>
              </div>
            </button>

            <Link
              href="/prompts"
              className="group px-6 py-4 bg-gradient-to-r from-zinc-900 to-zinc-800 text-white rounded-xl font-semibold hover:from-zinc-800 hover:to-zinc-700 transition-all shadow-lg hover:shadow-xl"
            >
              <div className="flex items-center justify-center gap-3">
                <span className="text-2xl">🤖</span>
                <div className="text-left">
                  <div className="font-bold">Agent Prompts</div>
                  <div className="text-xs text-zinc-300 font-normal">Customize AI behavior</div>
                </div>
              </div>
            </Link>

            <button
              onClick={clearAll}
              disabled={loading}
              className="group px-6 py-4 bg-white border-2 border-zinc-300 text-zinc-900 rounded-xl font-semibold hover:bg-zinc-50 hover:border-zinc-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <div className="flex items-center justify-center gap-3">
                <span className="text-2xl">🗑️</span>
                <div className="text-left">
                  <div className="font-bold">Clear Queue</div>
                  <div className="text-xs text-zinc-600 font-normal">Remove all posts</div>
                </div>
              </div>
            </button>
          </div>

          {msg && (
            <div
              className={`p-4 rounded-xl text-sm font-medium border-2 ${
                msg.includes("❌")
                  ? "bg-red-50 text-red-900 border-red-200"
                  : "bg-green-50 text-green-900 border-green-200"
              }`}
            >
              {msg}
            </div>
          )}
        </div>

        {/* Enhanced Statistics with Visual Metrics */}
        <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
          <h2 className="text-xl font-bold text-zinc-900 mb-5">Queue Analytics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
              <div className="text-3xl font-bold text-blue-900">{rows.length}</div>
              <div className="text-sm text-blue-700 font-medium mt-1">Total Posts</div>
              <div className="text-xs text-blue-600 mt-1">In approval queue</div>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
              <div className="text-3xl font-bold text-purple-900">{postsWithVideos}</div>
              <div className="text-sm text-purple-700 font-medium mt-1">With Videos</div>
              <div className="text-xs text-purple-600 mt-1">AI-generated clips</div>
            </div>

            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
              <div className="text-3xl font-bold text-green-900">{postsWithImages}</div>
              <div className="text-sm text-green-700 font-medium mt-1">With Images</div>
              <div className="text-xs text-green-600 mt-1">AI-generated visuals</div>
            </div>

            <div className="bg-gradient-to-br from-zinc-50 to-zinc-100 rounded-xl p-4 border border-zinc-200">
              <div className="text-3xl font-bold text-zinc-900">{rows.length - postsWithMedia}</div>
              <div className="text-sm text-zinc-700 font-medium mt-1">Text Only</div>
              <div className="text-xs text-zinc-600 mt-1">No media attached</div>
            </div>
          </div>
        </div>

        {/* Enhanced Content Queue with Better Organization */}
        <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-bold text-zinc-900">Approved Content Queue</h2>
              <p className="text-sm text-zinc-600 mt-1">
                Review and manage AI-generated posts ready for publishing
              </p>
            </div>
            <div className="px-4 py-2 bg-blue-50 text-blue-900 rounded-lg text-sm font-semibold border border-blue-200">
              {rows.length} Posts Ready
            </div>
          </div>

          {rows.length === 0 ? (
            <div className="text-center py-16 px-6">
              <div className="w-24 h-24 bg-zinc-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-5xl">📭</span>
              </div>
              <h3 className="text-xl font-bold text-zinc-900 mb-2">No Content in Queue</h3>
              <p className="text-zinc-600 mb-6 max-w-md mx-auto">
                Click the "Generate Content" button above to run the AI pipeline and create new posts with your
                configured agent prompts
              </p>
              <button
                onClick={runBatch}
                disabled={loading}
                className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50 transition-all inline-flex items-center gap-2"
              >
                <span className="text-xl">✨</span>
                Generate Your First Batch
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {rows.map((r) => {
                const displayContent = r.content || r.commentary || "";
                const full = [r.commentary, r.content].filter(Boolean).join("\n\n");

                const rawImageUrl = r.image_url;
                const imageUrl = resolveMediaUrl(rawImageUrl);
                const rawVideoUrl = r.video_url;
                const videoUrl = resolveMediaUrl(rawVideoUrl);

                const hasVideo = !!videoUrl && (r.has_video || !!r.video_url);
                const hasImage = !!imageUrl && !hasVideo;

                return (
                  <div
                    key={r.id}
                    className="border-2 border-zinc-200 rounded-xl p-5 bg-gradient-to-br from-white to-zinc-50 hover:shadow-lg transition-all"
                  >
                    {/* Enhanced Header with Better Tags */}
                    <div className="flex gap-2 flex-wrap mb-4 text-xs items-center">
                      <span className="px-3 py-1.5 bg-blue-600 text-white rounded-full font-bold">
                        {r.target_type}
                      </span>
                      <span className="px-3 py-1.5 bg-zinc-800 text-white rounded-full font-semibold">
                        {r.lifecycle}
                      </span>
                      {hasVideo && (
                        <span className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-full font-bold flex items-center gap-1">
                          <span>🎬</span>
                          <span>Video</span>
                        </span>
                      )}
                      {hasImage && (
                        <span className="px-3 py-1.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-full font-bold flex items-center gap-1">
                          <span>🖼️</span>
                          <span>Image</span>
                        </span>
                      )}
                      {r.media_provider === "huggingface" && (
                        <span className="px-3 py-1.5 bg-green-600 text-white rounded-full font-bold">
                          FREE TIER
                        </span>
                      )}
                      {r.media_cost !== undefined && r.media_cost > 0 && (
                        <span className="px-3 py-1.5 bg-amber-100 text-amber-900 rounded-full font-semibold">
                          ${r.media_cost.toFixed(3)}
                        </span>
                      )}
                      {r.created_at && (
                        <span className="ml-auto text-zinc-500 font-medium">
                          {new Date(r.created_at).toLocaleString()}
                        </span>
                      )}
                    </div>

                    {/* Video Display with Enhanced UI */}
                    {hasVideo && videoUrl && (
                      <div className="mb-5 rounded-xl overflow-hidden border-2 border-zinc-300 bg-black shadow-lg">
                        <video
                          controls
                          loop
                          muted
                          playsInline
                          className="w-full h-auto"
                          style={{ maxHeight: "520px" }}
                        >
                          <source src={videoUrl} type="video/mp4" />
                          Your browser does not support the video tag.
                        </video>
                        {(r.video_description || r.video_generation_time) && (
                          <div className="p-4 bg-zinc-900 text-zinc-100 text-xs space-y-2">
                            {r.video_description && (
                              <div className="flex gap-2">
                                <span className="font-bold text-white">Video:</span>
                                <span className="text-zinc-300">{r.video_description}</span>
                              </div>
                            )}
                            {r.video_generation_time && (
                              <div className="text-zinc-400 flex flex-wrap gap-3">
                                <span>⏱️ Generated in {r.video_generation_time}s</span>
                                {r.video_size_mb && <span>💾 {r.video_size_mb}MB</span>}
                                {r.media_cost !== undefined && (
                                  <span>💰 Cost: ${r.media_cost.toFixed(2)}</span>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Image Display with Enhanced UI */}
                    {hasImage && imageUrl && (
                      <div className="mb-5 rounded-xl overflow-hidden border-2 border-zinc-300 bg-white shadow-lg">
                        <div className="relative w-full" style={{ paddingTop: "56.25%" }}>
                          <img
                            src={imageUrl}
                            alt={r.image_description || "Generated image"}
                            className="absolute inset-0 w-full h-full object-cover"
                            loading="lazy"
                            decoding="async"
                            onError={(e) => {
                              const el = e.currentTarget as HTMLImageElement & { dataset: any };
                              const fname = (rawImageUrl?.split("/").pop() || "") as string;
                              if (fname && !el.dataset.fallback) {
                                el.dataset.fallback = "1";
                                el.src = `/images/${fname}`;
                              }
                            }}
                          />
                        </div>
                        {r.image_description && (
                          <div className="p-4 bg-zinc-50 border-t border-zinc-200">
                            <div className="flex gap-2 text-xs">
                              <span className="font-bold text-zinc-900">Image:</span>
                              <span className="text-zinc-700">{r.image_description}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Content with Better Typography */}
                    <div className="whitespace-pre-wrap mb-4 leading-relaxed text-sm text-zinc-900 bg-white rounded-lg p-4 border border-zinc-200">
                      {displayContent}
                    </div>

                    {/* Enhanced Hashtags */}
                    {r.hashtags?.length ? (
                      <div className="mb-4 flex gap-2 flex-wrap">
                        {r.hashtags.map((h, i) => (
                          <span
                            key={i}
                            className="text-xs bg-blue-100 text-blue-800 px-3 py-1.5 rounded-full font-semibold border border-blue-200"
                          >
                            #{h}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    {/* Status Messages with Better Visibility */}
                    {r.li_post_id && (
                      <div className="text-sm text-green-800 font-semibold mb-3 bg-green-50 p-3 rounded-lg border border-green-200">
                        ✅ Published Successfully • LinkedIn Post ID: {r.li_post_id}
                      </div>
                    )}
                    {r.error_message && (
                      <div className="text-sm text-red-800 bg-red-50 p-3 rounded-lg mb-3 border border-red-200">
                        ❌ Publication Error: {r.error_message}
                      </div>
                    )}

                    {/* Enhanced Action Buttons */}
                    <div className="flex gap-2 flex-wrap pt-3 border-t border-zinc-200">
                      <button
                        onClick={() => navigator.clipboard.writeText(displayContent)}
                        className="px-4 py-2 text-xs font-semibold border-2 border-zinc-300 rounded-lg hover:bg-zinc-100 hover:border-zinc-400 transition-all"
                      >
                        📋 Copy Text
                      </button>
                      <button
                        onClick={() => navigator.clipboard.writeText(full)}
                        className="px-4 py-2 text-xs font-semibold border-2 border-zinc-300 rounded-lg hover:bg-zinc-100 hover:border-zinc-400 transition-all"
                      >
                        📋 Copy with Tags
                      </button>

                      {/* Video Actions */}
                      {hasVideo && videoUrl && (
                        <>
                          <button
                            onClick={() => window.open(videoUrl, "_blank")}
                            className="px-4 py-2 text-xs font-semibold border-2 border-purple-300 bg-purple-50 text-purple-900 rounded-lg hover:bg-purple-100 transition-all"
                          >
                            🎬 Open Video
                          </button>
                          <a
                            href={videoUrl}
                            download={`video-${r.id}.mp4`}
                            className="px-4 py-2 text-xs font-semibold border-2 border-purple-300 bg-purple-50 text-purple-900 rounded-lg hover:bg-purple-100 transition-all inline-flex items-center"
                          >
                            💾 Download Video
                          </a>
                          {r.video_prompt && (
                            <button
                              onClick={() => {
                                const info = `Video Generation Details\n${"=".repeat(40)}\n\nPrompt: ${
                                  r.video_prompt
                                }\n\nDescription: ${r.video_description || "N/A"}\n\nGeneration Time: ${
                                  r.video_generation_time || "N/A"
                                }s\n\nFile Size: ${r.video_size_mb || "N/A"}MB\n\nProvider: ${
                                  r.media_provider || "N/A"
                                }\n\nCost: $${r.media_cost?.toFixed(2) || "0.00"}`;
                                alert(info);
                              }}
                              className="px-4 py-2 text-xs font-semibold border-2 border-zinc-300 rounded-lg hover:bg-zinc-100 transition-all"
                            >
                              ℹ️ Video Details
                            </button>
                          )}
                        </>
                      )}

                      {/* Image Actions */}
                      {hasImage && imageUrl && (
                        <>
                          <button
                            onClick={() => window.open(imageUrl, "_blank")}
                            className="px-4 py-2 text-xs font-semibold border-2 border-blue-300 bg-blue-50 text-blue-900 rounded-lg hover:bg-blue-100 transition-all"
                          >
                            🖼️ Open Image
                          </button>
                          {r.image_prompt && (
                            <button
                              onClick={() => {
                                const info = `Image Generation Details\n${"=".repeat(40)}\n\nPrompt: ${
                                  r.image_prompt
                                }\n\nDescription: ${r.image_description || "N/A"}`;
                                alert(info);
                              }}
                              className="px-4 py-2 text-xs font-semibold border-2 border-zinc-300 rounded-lg hover:bg-zinc-100 transition-all"
                            >
                              ℹ️ Image Details
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}