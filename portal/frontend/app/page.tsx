// portal/frontend/app/page.tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import CostDashboard from "@/components/CostDashboard";

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

  return (
    <main 
      className="min-h-screen relative overflow-x-hidden"
      style={{
        background: 'linear-gradient(180deg, #f6f9fc 0%, #ffffff 100%)',
      }}
    >
      <div className="relative max-w-7xl mx-auto px-6 py-12 space-y-8">
        {/* Stripe-style Header */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-8 md:p-12">
            <div className="flex items-start justify-between gap-8 mb-6">
              <div className="flex-1">
                <div className="flex items-center gap-4 mb-3">
                  <div 
                    className="w-12 h-12 rounded-lg flex items-center justify-center shadow-sm"
                    style={{
                      background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                    }}
                  >
                    <span className="text-white text-xl font-semibold">JE</span>
                  </div>
                  <div>
                    <h1 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-1">
                      Content Studio
                    </h1>
                    <p className="text-sm text-gray-500">
                      Jesse A. Eisenbalm · LinkedIn Content Creation
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600 mt-4 ml-16">
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-md border border-gray-200">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>
                      {me?.name || me?.sub || "Loading..."}
                    </span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowWorkflowGuide(!showWorkflowGuide)}
                className="px-4 py-2 bg-white hover:bg-gray-50 text-gray-700 rounded-lg text-sm font-medium border border-gray-300 transition-all duration-200"
              >
                {showWorkflowGuide ? "Hide" : "Show"} Workflow
              </button>
            </div>

            {/* Stripe-style Workflow Guide */}
            {showWorkflowGuide && (
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-8 border border-purple-100 mt-6">
                <h3 className="text-2xl font-semibold text-gray-900 mb-6">
                  How it works
                </h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
                    <div className="flex items-start gap-4">
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-white font-semibold"
                        style={{ background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)' }}
                      >
                        1
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">Guided Creation</h4>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          Follow our intuitive five-step wizard to customize brand voice, select inspiration sources, 
                          and define your target audience with precision
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
                    <div className="flex items-start gap-4">
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-white font-semibold"
                        style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #6366F1 100%)' }}
                      >
                        2
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">AI-Powered Content</h4>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          Choose from trending topics, cultural references, or philosophical themes. 
                          Our AI transforms these into compelling narratives
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
                    <div className="flex items-start gap-4">
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-white font-semibold"
                        style={{ background: 'linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)' }}
                      >
                        3
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">Bespoke Imagery</h4>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          Each post features custom AI-generated visuals incorporating your brand's 
                          signature messaging and aesthetic
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-100">
                    <div className="flex items-start gap-4">
                      <div 
                        className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 text-white font-semibold"
                        style={{ background: 'linear-gradient(135deg, #10B981 0%, #059669 100%)' }}
                      >
                        4
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900 mb-2">Expert Validation</h4>
                        <p className="text-sm text-gray-600 leading-relaxed">
                          Content undergoes rigorous review by three expert validators ensuring 
                          quality, tone, compliance, and brand alignment
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Stripe-style Content Queue */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-8 md:p-12">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">Your content</h2>
                <p className="text-gray-600">
                  Your curated content library
                </p>
              </div>
              <div className="px-4 py-2 bg-purple-50 text-purple-700 rounded-lg text-sm font-medium border border-purple-200">
                {rows.length} {rows.length === 1 ? 'Post' : 'Posts'}
              </div>
            </div>

            {rows.length === 0 ? (
              <div className="text-center py-20 px-6">
                <div 
                  className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg"
                  style={{
                    background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                  }}
                >
                  <span className="text-4xl">✨</span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-3">Create your first post</h3>
                <p className="text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
                  Use our guided wizard to create engaging LinkedIn content with AI-generated imagery
                </p>
                <Link
                  href="/wizard"
                  className="inline-flex items-center gap-3 px-8 py-4 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 text-base"
                  style={{
                    background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                  }}
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
                      className="border border-gray-200 rounded-xl p-6 md:p-8 bg-white shadow-sm hover:shadow-md transition-all duration-300"
                    >
                      {/* Header */}
                      <div className="flex gap-2 flex-wrap mb-6 text-xs items-center">
                        <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-md font-medium">
                          {r.target_type}
                        </span>
                        <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md font-medium">
                          {r.lifecycle}
                        </span>
                        {hasVideo && (
                          <span className="px-3 py-1.5 bg-pink-100 text-pink-700 rounded-md font-medium">
                            Video
                          </span>
                        )}
                        {hasImage && (
                          <span className="px-3 py-1.5 bg-cyan-100 text-cyan-700 rounded-md font-medium">
                            Image
                          </span>
                        )}
                        {r.media_provider === "huggingface" && (
                          <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-md font-medium">
                            Free Tier
                          </span>
                        )}
                        {r.media_cost !== undefined && r.media_cost > 0 && (
                          <span className="px-3 py-1.5 bg-amber-100 text-amber-700 rounded-md font-medium">
                            ${r.media_cost.toFixed(3)}
                          </span>
                        )}
                        {r.created_at && (
                          <span className="ml-auto text-gray-500 text-[10px] font-medium">
                            {new Date(r.created_at).toLocaleString()}
                          </span>
                        )}
                      </div>

                      {/* Video Display */}
                      {hasVideo && videoUrl && (
                        <div className="mb-6 rounded-xl overflow-hidden border border-gray-200 bg-gray-50 shadow-sm">
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
                            <div className="p-4 bg-white text-gray-700 text-xs space-y-2">
                              {r.video_description && (
                                <div className="flex gap-2">
                                  <span className="font-semibold text-gray-900">Description:</span>
                                  <span className="text-gray-600">{r.video_description}</span>
                                </div>
                              )}
                              {r.video_generation_time && (
                                <div className="text-gray-500 flex flex-wrap gap-3">
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
                        <div className="mb-6 rounded-xl overflow-hidden border border-gray-200 bg-gray-50 shadow-sm">
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
                            <div className="p-4 bg-white border-t border-gray-200">
                              <div className="flex gap-2 text-xs">
                                <span className="font-semibold text-gray-900">Description:</span>
                                <span className="text-gray-600">{r.image_description}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Content */}
                      <div className="whitespace-pre-wrap mb-6 leading-relaxed text-sm text-gray-800 bg-gray-50 rounded-lg p-6 border border-gray-200">
                        {displayContent}
                      </div>

                      {/* Hashtags */}
                      {r.hashtags?.length ? (
                        <div className="mb-6 flex gap-2 flex-wrap">
                          {r.hashtags.map((h, i) => (
                            <span
                              key={i}
                              className="text-xs bg-purple-50 text-purple-600 px-3 py-1.5 rounded-md font-medium border border-purple-200"
                            >
                              #{h}
                            </span>
                          ))}
                        </div>
                      ) : null}

                      {/* Status Messages */}
                      {r.li_post_id && (
                        <div className="text-sm text-green-700 font-medium mb-4 bg-green-50 p-4 rounded-lg border border-green-200">
                          ✅ Published · Post ID: {r.li_post_id}
                        </div>
                      )}
                      {r.error_message && (
                        <div className="text-sm text-red-700 bg-red-50 p-4 rounded-lg mb-4 border border-red-200 font-medium">
                          ❌ Error: {r.error_message}
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2 flex-wrap pt-6 border-t border-gray-200">
                        <button
                          onClick={() => navigator.clipboard.writeText(displayContent)}
                          className="px-4 py-2 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 text-gray-700"
                        >
                          Copy Text
                        </button>
                        <button
                          onClick={() => navigator.clipboard.writeText(full)}
                          className="px-4 py-2 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 text-gray-700"
                        >
                          Copy Full
                        </button>

                        {/* Video Actions */}
                        {hasVideo && videoUrl && (
                          <>
                            <button
                              onClick={() => window.open(videoUrl, "_blank")}
                              className="px-4 py-2 text-xs font-medium border border-pink-200 bg-pink-50 text-pink-700 rounded-lg hover:bg-pink-100 transition-all duration-200"
                            >
                              Open Video
                            </button>
                            <a
                              href={videoUrl}
                              download={`video-${r.id}.mp4`}
                              className="px-4 py-2 text-xs font-medium border border-pink-200 bg-pink-50 text-pink-700 rounded-lg hover:bg-pink-100 transition-all duration-200 inline-flex items-center"
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
                                className="px-4 py-2 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 text-gray-700"
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
                              className="px-4 py-2 text-xs font-medium border border-cyan-200 bg-cyan-50 text-cyan-700 rounded-lg hover:bg-cyan-100 transition-all duration-200"
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
                                className="px-4 py-2 text-xs font-medium border border-gray-300 rounded-lg hover:bg-gray-50 transition-all duration-200 text-gray-700"
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

        {/* Cost Dashboard - Moved to Bottom */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-8 md:p-12">
            <CostDashboard />
          </div>
        </div>
      </div>
    </main>
  );
}