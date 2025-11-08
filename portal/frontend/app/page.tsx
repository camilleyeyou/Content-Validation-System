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

  async function clearAll() {
    if (!confirm("⚠️ This will permanently delete all saved posts. Continue?")) return;
    setMsg("");
    setLoading(true);
    try {
      const data = await fetchJSON(`${API_BASE}/api/approved/clear`, { method: "POST" });
      setMsg(`✅ Successfully cleared ${data.deleted} posts`);
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
    <main 
      className="min-h-screen relative overflow-x-hidden"
      style={{
        background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)',
      }}
    >
      {/* Subtle grain texture overlay */}
      <div className="fixed inset-0 opacity-[0.015] pointer-events-none" 
        style={{
          backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 400 400\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.9\' numOctaves=\'4\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\'/%3E%3C/svg%3E")',
        }}
      ></div>

      <div className="relative max-w-[1400px] mx-auto px-8 py-16 space-y-12">
        {/* Elegant Header */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
          <div className="p-12">
            <div className="flex items-start justify-between gap-8 mb-8">
              <div className="flex-1">
                <div className="flex items-center gap-5 mb-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-[#d4af37] via-[#f4e4c1] to-[#d4af37] rounded-sm flex items-center justify-center shadow-lg">
                    <span className="text-black text-3xl font-serif font-bold">JE</span>
                  </div>
                  <div>
                    <h1 className="text-5xl font-serif font-light text-white tracking-wider mb-2">
                      Content Studio
                    </h1>
                    <p className="text-[#d4af37] text-sm tracking-[0.2em] uppercase font-light">
                      Jesse A. Eisenbalm · LinkedIn Content Creation
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-400 mt-6 ml-[84px]">
                  <div className="flex items-center gap-3 px-4 py-2 bg-[#d4af37]/10 rounded-sm border border-[#d4af37]/30">
                    <div className="w-1.5 h-1.5 bg-[#d4af37] rounded-full"></div>
                    <span className="font-light">
                      <span className="text-gray-500">Authenticated as</span>{" "}
                      <span className="font-normal text-[#d4af37]">{me?.name || me?.sub || "Loading..."}</span>
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowWorkflowGuide(!showWorkflowGuide)}
                className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-sm text-sm font-light tracking-wider uppercase border border-white/10 hover:border-[#d4af37]/50 transition-all duration-300"
              >
                {showWorkflowGuide ? "Hide" : "Show"} Workflow
              </button>
            </div>

            {/* Refined Workflow Guide */}
            {showWorkflowGuide && (
              <div className="bg-gradient-to-br from-[#d4af37]/5 to-transparent rounded-sm p-8 border border-[#d4af37]/20 mt-8">
                <h3 className="text-2xl font-serif font-light text-white mb-8 tracking-wide">
                  The Process
                </h3>
                <div className="grid md:grid-cols-2 gap-8">
                  <div className="space-y-6">
                    <div className="bg-black/40 backdrop-blur-sm rounded-sm p-6 border border-white/5 hover:border-[#d4af37]/30 transition-all duration-300">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 border border-[#d4af37] text-[#d4af37] rounded-sm flex items-center justify-center font-serif text-sm flex-shrink-0">
                          I
                        </div>
                        <div>
                          <h4 className="font-serif text-white mb-2 text-lg">Guided Creation</h4>
                          <p className="text-sm text-gray-400 font-light leading-relaxed">
                            Follow our intuitive five-step wizard to customize brand voice, select inspiration sources, 
                            and define your target audience with precision
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-black/40 backdrop-blur-sm rounded-sm p-6 border border-white/5 hover:border-[#d4af37]/30 transition-all duration-300">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 border border-[#d4af37] text-[#d4af37] rounded-sm flex items-center justify-center font-serif text-sm flex-shrink-0">
                          II
                        </div>
                        <div>
                          <h4 className="font-serif text-white mb-2 text-lg">AI-Powered Content</h4>
                          <p className="text-sm text-gray-400 font-light leading-relaxed">
                            Choose from trending topics, cultural references, or philosophical themes. 
                            Our AI transforms these into compelling narratives
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-black/40 backdrop-blur-sm rounded-sm p-6 border border-white/5 hover:border-[#d4af37]/30 transition-all duration-300">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 border border-[#d4af37] text-[#d4af37] rounded-sm flex items-center justify-center font-serif text-sm flex-shrink-0">
                          III
                        </div>
                        <div>
                          <h4 className="font-serif text-white mb-2 text-lg">Bespoke Imagery</h4>
                          <p className="text-sm text-gray-400 font-light leading-relaxed">
                            Each post features custom AI-generated visuals incorporating your brand's 
                            signature messaging and aesthetic
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="bg-black/40 backdrop-blur-sm rounded-sm p-6 border border-white/5 hover:border-[#d4af37]/30 transition-all duration-300">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 border border-[#d4af37] text-[#d4af37] rounded-sm flex items-center justify-center font-serif text-sm flex-shrink-0">
                          IV
                        </div>
                        <div>
                          <h4 className="font-serif text-white mb-2 text-lg">Expert Validation</h4>
                          <p className="text-sm text-gray-400 font-light leading-relaxed">
                            Content undergoes rigorous review by three expert validators ensuring 
                            quality, tone, compliance, and brand alignment
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-black/40 backdrop-blur-sm rounded-sm p-6 border border-white/5 hover:border-[#d4af37]/30 transition-all duration-300">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 border border-[#d4af37] text-[#d4af37] rounded-sm flex items-center justify-center font-serif text-sm flex-shrink-0">
                          V
                        </div>
                        <div>
                          <h4 className="font-serif text-white mb-2 text-lg">Seamless Publishing</h4>
                          <p className="text-sm text-gray-400 font-light leading-relaxed">
                            Review your curated content with full preview capabilities, 
                            then publish directly to LinkedIn when ready
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gradient-to-br from-[#d4af37]/10 to-transparent rounded-sm p-6 border border-[#d4af37]/30">
                      <p className="text-xs text-[#d4af37] font-light leading-relaxed italic">
                        "Customize AI behavior in Settings to match your unique voice and style preferences"
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Refined Actions */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
          <div className="p-10">
            <div className="mb-10">
              <h2 className="text-3xl font-serif font-light text-white tracking-wide mb-2">Create</h2>
              <p className="text-sm text-gray-400 font-light tracking-wide">Craft exceptional LinkedIn content</p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              <Link
                href="/wizard"
                className="group relative px-10 py-12 bg-gradient-to-br from-[#d4af37] to-[#b8941f] text-black rounded-sm font-light hover:shadow-2xl hover:shadow-[#d4af37]/20 transition-all duration-500 overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                <div className="relative">
                  <div className="text-xl font-serif mb-3 tracking-wide">New Post</div>
                  <div className="text-xs uppercase tracking-widest opacity-70">Guided Creation</div>
                </div>
              </Link>

              <Link
                href="/prompts"
                className="group px-10 py-12 bg-white/5 hover:bg-white/10 text-white rounded-sm font-light border border-white/10 hover:border-[#d4af37]/50 transition-all duration-500"
              >
                <div className="text-xl font-serif mb-3 tracking-wide">Settings</div>
                <div className="text-xs uppercase tracking-widest text-gray-400">AI Configuration</div>
              </Link>

              <button
                onClick={clearAll}
                disabled={loading}
                className="group px-10 py-12 bg-white/5 hover:bg-red-900/20 text-white rounded-sm font-light border border-white/10 hover:border-red-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-500"
              >
                <div className="text-xl font-serif mb-3 tracking-wide">Clear All</div>
                <div className="text-xs uppercase tracking-widest text-gray-400">Remove Posts</div>
              </button>
            </div>

            {msg && (
              <div
                className={`mt-8 p-5 rounded-sm text-sm font-light border ${
                  msg.includes("❌")
                    ? "bg-red-900/20 text-red-300 border-red-500/30"
                    : "bg-emerald-900/20 text-emerald-300 border-emerald-500/30"
                }`}
              >
                {msg}
              </div>
            )}
          </div>
        </div>

        {/* Elegant Statistics */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
          <div className="p-10">
            <h2 className="text-3xl font-serif font-light text-white tracking-wide mb-8">Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="bg-gradient-to-br from-[#d4af37]/10 to-transparent rounded-sm p-6 border border-[#d4af37]/20 hover:border-[#d4af37]/40 transition-all duration-300">
                <div className="text-5xl font-serif font-light text-[#d4af37] mb-2">{rows.length}</div>
                <div className="text-xs uppercase tracking-widest text-gray-400 mb-1">Total Posts</div>
                <div className="text-[10px] text-gray-500 font-light">In queue</div>
              </div>

              <div className="bg-white/5 rounded-sm p-6 border border-white/10 hover:border-purple-500/30 transition-all duration-300">
                <div className="text-5xl font-serif font-light text-purple-300 mb-2">{postsWithVideos}</div>
                <div className="text-xs uppercase tracking-widest text-gray-400 mb-1">Videos</div>
                <div className="text-[10px] text-gray-500 font-light">AI-generated</div>
              </div>

              <div className="bg-white/5 rounded-sm p-6 border border-white/10 hover:border-blue-500/30 transition-all duration-300">
                <div className="text-5xl font-serif font-light text-blue-300 mb-2">{postsWithImages}</div>
                <div className="text-xs uppercase tracking-widest text-gray-400 mb-1">Images</div>
                <div className="text-[10px] text-gray-500 font-light">AI-generated</div>
              </div>

              <div className="bg-white/5 rounded-sm p-6 border border-white/10 hover:border-gray-500/30 transition-all duration-300">
                <div className="text-5xl font-serif font-light text-gray-300 mb-2">{rows.length - postsWithMedia}</div>
                <div className="text-xs uppercase tracking-widest text-gray-400 mb-1">Text Only</div>
                <div className="text-[10px] text-gray-500 font-light">No media</div>
              </div>
            </div>
          </div>
        </div>

        {/* Refined Content Queue */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
          <div className="p-10">
            <div className="flex items-center justify-between mb-10">
              <div>
                <h2 className="text-3xl font-serif font-light text-white tracking-wide mb-2">Collection</h2>
                <p className="text-sm text-gray-400 font-light tracking-wide">
                  Your curated content library
                </p>
              </div>
              <div className="px-6 py-2 bg-[#d4af37]/10 text-[#d4af37] rounded-sm text-sm font-light border border-[#d4af37]/30">
                {rows.length} {rows.length === 1 ? 'Post' : 'Posts'}
              </div>
            </div>

            {rows.length === 0 ? (
              <div className="text-center py-24 px-6">
                <div className="w-32 h-32 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-white/10">
                  <span className="text-6xl">✨</span>
                </div>
                <h3 className="text-3xl font-serif font-light text-white mb-4 tracking-wide">Begin Your Journey</h3>
                <p className="text-gray-400 font-light mb-10 max-w-md mx-auto leading-relaxed">
                  Create your first post using our guided wizard with AI-generated imagery
                </p>
                <Link
                  href="/wizard"
                  className="inline-flex items-center gap-4 px-12 py-5 bg-gradient-to-br from-[#d4af37] to-[#b8941f] text-black rounded-sm font-light hover:shadow-2xl hover:shadow-[#d4af37]/20 transition-all duration-500 text-lg tracking-wide"
                >
                  Start Creating
                </Link>
              </div>
            ) : (
              <div className="space-y-6">
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
                      className="border border-white/10 rounded-sm p-8 bg-black/30 backdrop-blur-sm hover:border-[#d4af37]/30 transition-all duration-500"
                    >
                      {/* Refined Header */}
                      <div className="flex gap-3 flex-wrap mb-6 text-xs items-center">
                        <span className="px-4 py-1.5 bg-[#d4af37]/20 text-[#d4af37] rounded-sm font-light uppercase tracking-wider border border-[#d4af37]/30">
                          {r.target_type}
                        </span>
                        <span className="px-4 py-1.5 bg-white/10 text-gray-300 rounded-sm font-light uppercase tracking-wider border border-white/20">
                          {r.lifecycle}
                        </span>
                        {hasVideo && (
                          <span className="px-4 py-1.5 bg-purple-500/20 text-purple-300 rounded-sm font-light uppercase tracking-wider border border-purple-500/30">
                            Video
                          </span>
                        )}
                        {hasImage && (
                          <span className="px-4 py-1.5 bg-blue-500/20 text-blue-300 rounded-sm font-light uppercase tracking-wider border border-blue-500/30">
                            Image
                          </span>
                        )}
                        {r.media_provider === "huggingface" && (
                          <span className="px-4 py-1.5 bg-emerald-500/20 text-emerald-300 rounded-sm font-light uppercase tracking-wider border border-emerald-500/30">
                            Free Tier
                          </span>
                        )}
                        {r.media_cost !== undefined && r.media_cost > 0 && (
                          <span className="px-4 py-1.5 bg-amber-500/20 text-amber-300 rounded-sm font-light tracking-wider border border-amber-500/30">
                            ${r.media_cost.toFixed(3)}
                          </span>
                        )}
                        {r.created_at && (
                          <span className="ml-auto text-gray-500 font-light text-[10px] uppercase tracking-widest">
                            {new Date(r.created_at).toLocaleString()}
                          </span>
                        )}
                      </div>

                      {/* Video Display */}
                      {hasVideo && videoUrl && (
                        <div className="mb-6 rounded-sm overflow-hidden border border-white/20 bg-black shadow-2xl">
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
                            <div className="p-5 bg-black/80 backdrop-blur-sm text-gray-300 text-xs space-y-2 font-light">
                              {r.video_description && (
                                <div className="flex gap-3">
                                  <span className="font-normal text-white">Description:</span>
                                  <span className="text-gray-400">{r.video_description}</span>
                                </div>
                              )}
                              {r.video_generation_time && (
                                <div className="text-gray-500 flex flex-wrap gap-4">
                                  <span>⏱️ {r.video_generation_time}s</span>
                                  {r.video_size_mb && <span>💾 {r.video_size_mb}MB</span>}
                                  {r.media_cost !== undefined && (
                                    <span>💰 ${r.media_cost.toFixed(2)}</span>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Image Display */}
                      {hasImage && imageUrl && (
                        <div className="mb-6 rounded-sm overflow-hidden border border-white/20 bg-black shadow-2xl">
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
                            <div className="p-5 bg-black/80 backdrop-blur-sm border-t border-white/10">
                              <div className="flex gap-3 text-xs font-light">
                                <span className="font-normal text-white">Description:</span>
                                <span className="text-gray-400">{r.image_description}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Content */}
                      <div className="whitespace-pre-wrap mb-6 leading-relaxed text-sm text-gray-200 bg-black/40 rounded-sm p-6 border border-white/5 font-light">
                        {displayContent}
                      </div>

                      {/* Hashtags */}
                      {r.hashtags?.length ? (
                        <div className="mb-6 flex gap-2 flex-wrap">
                          {r.hashtags.map((h, i) => (
                            <span
                              key={i}
                              className="text-xs bg-[#d4af37]/10 text-[#d4af37] px-3 py-1.5 rounded-sm font-light border border-[#d4af37]/30"
                            >
                              #{h}
                            </span>
                          ))}
                        </div>
                      ) : null}

                      {/* Status Messages */}
                      {r.li_post_id && (
                        <div className="text-sm text-emerald-300 font-light mb-4 bg-emerald-900/20 p-4 rounded-sm border border-emerald-500/30">
                          ✅ Published · Post ID: {r.li_post_id}
                        </div>
                      )}
                      {r.error_message && (
                        <div className="text-sm text-red-300 bg-red-900/20 p-4 rounded-sm mb-4 border border-red-500/30 font-light">
                          ❌ Error: {r.error_message}
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-3 flex-wrap pt-6 border-t border-white/10">
                        <button
                          onClick={() => navigator.clipboard.writeText(displayContent)}
                          className="px-4 py-2 text-xs font-light border border-white/10 rounded-sm hover:bg-white/5 hover:border-[#d4af37]/30 transition-all duration-300 uppercase tracking-wider"
                        >
                          Copy Text
                        </button>
                        <button
                          onClick={() => navigator.clipboard.writeText(full)}
                          className="px-4 py-2 text-xs font-light border border-white/10 rounded-sm hover:bg-white/5 hover:border-[#d4af37]/30 transition-all duration-300 uppercase tracking-wider"
                        >
                          Copy Full
                        </button>

                        {/* Video Actions */}
                        {hasVideo && videoUrl && (
                          <>
                            <button
                              onClick={() => window.open(videoUrl, "_blank")}
                              className="px-4 py-2 text-xs font-light border border-purple-500/30 bg-purple-500/10 text-purple-300 rounded-sm hover:bg-purple-500/20 transition-all duration-300 uppercase tracking-wider"
                            >
                              Open Video
                            </button>
                            <a
                              href={videoUrl}
                              download={`video-${r.id}.mp4`}
                              className="px-4 py-2 text-xs font-light border border-purple-500/30 bg-purple-500/10 text-purple-300 rounded-sm hover:bg-purple-500/20 transition-all duration-300 inline-flex items-center uppercase tracking-wider"
                            >
                              Download
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
                                className="px-4 py-2 text-xs font-light border border-white/10 rounded-sm hover:bg-white/5 transition-all duration-300 uppercase tracking-wider"
                              >
                                Details
                              </button>
                            )}
                          </>
                        )}

                        {/* Image Actions */}
                        {hasImage && imageUrl && (
                          <>
                            <button
                              onClick={() => window.open(imageUrl, "_blank")}
                              className="px-4 py-2 text-xs font-light border border-blue-500/30 bg-blue-500/10 text-blue-300 rounded-sm hover:bg-blue-500/20 transition-all duration-300 uppercase tracking-wider"
                            >
                              Open Image
                            </button>
                            {r.image_prompt && (
                              <button
                                onClick={() => {
                                  const info = `Image Generation Details\n${"=".repeat(40)}\n\nPrompt: ${
                                    r.image_prompt
                                  }\n\nDescription: ${r.image_description || "N/A"}`;
                                  alert(info);
                                }}
                                className="px-4 py-2 text-xs font-light border border-white/10 rounded-sm hover:bg-white/5 transition-all duration-300 uppercase tracking-wider"
                              >
                                Details
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
      </div>
    </main>
  );
}