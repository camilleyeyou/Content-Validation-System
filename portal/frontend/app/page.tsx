// portal/frontend/app/page.tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ChevronRight } from "lucide-react";
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
  const [showcasePosts, setShowcasePosts] = useState<PostRow[]>([]);
  const [selectedPost, setSelectedPost] = useState<PostRow | null>(null);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [isPageReady, setIsPageReady] = useState(false);

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

  async function loadShowcase() {
    try {
      // Get all approved posts
      const allPosts = await fetchJSON(`${API_BASE}/api/approved`);
      
      // Filter to only posts with images and valid image URLs
      const postsWithImages = allPosts.filter((post: PostRow) => {
        const hasImage = post.image_url && post.image_url.length > 0;
        const notTestImage = post.image_url && !post.image_url.includes('example.com');
        return hasImage && notTestImage;
      });
      
      // Daily rotation logic
      if (postsWithImages.length <= 3) {
        // If 3 or fewer posts, show all
        setShowcasePosts(postsWithImages);
      } else {
        // Rotate posts based on current day
        const today = new Date();
        const dayOfYear = Math.floor((today.getTime() - new Date(today.getFullYear(), 0, 0).getTime()) / 86400000);
        
        // Use day of year to create a deterministic rotation
        const startIndex = dayOfYear % postsWithImages.length;
        
        // Select 3 posts starting from the rotated index
        const rotatedPosts = [];
        for (let i = 0; i < 3 && i < postsWithImages.length; i++) {
          const index = (startIndex + i) % postsWithImages.length;
          rotatedPosts.push(postsWithImages[index]);
        }
        
        setShowcasePosts(rotatedPosts);
      }
    } catch {}
  }

  useEffect(() => {
    loadMe();
    loadPosts();
    loadShowcase();
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
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="relative h-screen overflow-hidden flex items-center justify-center" role="banner">
        <div className="absolute inset-0 w-full h-full">
          <video
            autoPlay
            loop
            muted
            playsInline
            preload="auto"
            className={`absolute w-full h-full object-cover transition-opacity duration-1000 ${videoLoaded ? 'opacity-100' : 'opacity-0'}`}
            onLoadedData={() => setVideoLoaded(true)}
            onCanPlayThrough={() => {
              setVideoLoaded(true);
              setIsPageReady(true);
            }}
            poster="https://cdn.jsdelivr.net/gh/camilleyeyou/jesse-eisenbalm@main/public/images/hero-poster.jpg"
          >
            <source src="https://cdn.jsdelivr.net/gh/camilleyeyou/jesse-eisenbalm@main/public/videos/hero-background.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
          <div className="absolute inset-0 bg-black/60"></div>
        </div>

        <div className="relative z-10 max-w-4xl mx-auto text-center px-6">
          <h2 className="text-7xl md:text-9xl font-light text-white mb-8 tracking-tight leading-none">
            ARE THESE<br />MY REAL LIPS?
          </h2>

          <p className="text-xl md:text-2xl text-white/90 mb-4 font-light tracking-widest">
            STOP. BREATHE. BALM.
          </p>

          <p className="text-base md:text-lg text-white/80 mb-12 max-w-xl mx-auto font-light leading-relaxed">
            A human-only ritual for an AI-everywhere world. <br />
            Limited Edition.<br /> 
            Release 001. <br /> 
            All proceeds go to charity. 
          </p>

          <div className="flex flex-col sm:flex-row justify-center gap-4">
            <a 
              href="https://www.jesseaeisenbalm.com/#product" 
              className="bg-white text-black px-12 py-4 text-sm tracking-[0.2em] hover:bg-gray-50 transition-all inline-flex items-center justify-center group border border-white/20"
            >
              BUY NOW
              <ChevronRight size={16} className="ml-2 group-hover:translate-x-1 transition-transform" strokeWidth={1.5} />
            </a>
          </div>
        </div>
      </section>

      {/* Content Studio Section */}
      <div 
        className="relative overflow-x-hidden"
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

        {/* Campaign Examples Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-8 md:p-12">
            <div className="flex items-start justify-between mb-8">
              <div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Inspiration Gallery
                </h2>
                <p className="text-gray-600">
                  Fresh picks daily · Click any post to view details
                </p>
              </div>
              {showcasePosts.length > 0 && (
                <div className="flex flex-col items-end gap-2">
                  <div className="px-4 py-2 bg-purple-50 text-purple-700 rounded-lg text-sm font-medium border border-purple-200">
                    {showcasePosts.length} {showcasePosts.length === 1 ? 'Post' : 'Posts'}
                  </div>
                  <div className="text-xs text-gray-500 flex items-center gap-1">
                    <span>🔄</span>
                    <span>Rotates daily</span>
                  </div>
                </div>
              )}
            </div>

            {showcasePosts.length === 0 ? (
              <div className="text-center py-20 px-6">
                <div 
                  className="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg"
                  style={{
                    background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                  }}
                >
                  <span className="text-4xl">🎨</span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-3">No posts yet</h3>
                <p className="text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
                  Generate your first post with AI-powered content and images
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
              <>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {showcasePosts.map((post) => {
                    const imageUrl = resolveMediaUrl(post.image_url);
                    const displayContent = post.content || post.commentary || "";
                    
                    return (
                      <div 
                        key={post.id} 
                        onClick={() => setSelectedPost(post)}
                        className="border border-gray-200 rounded-xl overflow-hidden bg-gradient-to-br from-gray-50 to-white hover:shadow-lg hover:border-purple-300 transition-all duration-300 cursor-pointer"
                      >
                        {/* Thumbnail Image */}
                        {imageUrl && (
                          <div className="relative w-full h-48 bg-gray-100">
                            <img
                              src={imageUrl}
                              alt={post.image_description || "Generated image"}
                              className="w-full h-full object-cover"
                              loading="lazy"
                              onError={(e) => {
                                const el = e.currentTarget as HTMLImageElement & { dataset: any };
                                const fname = (post.image_url?.split("/").pop() || "") as string;
                                if (fname && !el.dataset.fallback) {
                                  el.dataset.fallback = "1";
                                  el.src = `/images/${fname}`;
                                }
                              }}
                            />
                          </div>
                        )}

                        <div className="p-6">
                          {/* Post Type Badge */}
                          <div className="flex items-center gap-2 mb-4">
                            <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-md font-medium text-xs">
                              {post.target_type}
                            </span>
                            <span className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md font-medium text-xs">
                              {post.lifecycle}
                            </span>
                          </div>

                          {/* Content Preview */}
                          <div className="bg-white p-4 rounded-lg border border-gray-200 mb-4 min-h-[140px]">
                            <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed line-clamp-6">
                              {displayContent}
                            </p>
                          </div>

                          {/* Hashtags */}
                          {post.hashtags && post.hashtags.length > 0 && (
                            <div className="flex flex-wrap gap-2 text-xs mb-4">
                              {post.hashtags.slice(0, 3).map((tag, i) => (
                                <span
                                  key={i}
                                  className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md font-medium"
                                >
                                  #{tag}
                                </span>
                              ))}
                              {post.hashtags.length > 3 && (
                                <span className="px-3 py-1.5 bg-gray-100 text-gray-600 rounded-md font-medium">
                                  +{post.hashtags.length - 3}
                                </span>
                              )}
                            </div>
                          )}

                          {/* Metadata */}
                          <div className="flex flex-wrap gap-2 text-xs">
                            {post.media_provider === "huggingface" && (
                              <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-md font-medium">
                                Free Tier
                              </span>
                            )}
                            {post.media_cost !== undefined && post.media_cost > 0 && (
                              <span className="px-3 py-1.5 bg-amber-100 text-amber-700 rounded-md font-medium">
                                ${post.media_cost.toFixed(3)}
                              </span>
                            )}
                          </div>

                          {/* View Details Button */}
                          <div className="mt-4 pt-4 border-t border-gray-200">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPost(post);
                              }}
                              className="w-full px-4 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-lg text-xs font-medium border border-purple-200 hover:border-purple-300 transition-all duration-200 flex items-center justify-center gap-2"
                            >
                              <span>View Details</span>
                              <span>→</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="text-center mt-8 pt-8 border-t border-gray-200">
                  <Link
                    href="/wizard"
                    className="inline-flex items-center gap-3 px-8 py-4 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 text-base"
                    style={{
                      background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                    }}
                  >
                    Create Your Own Content
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Cost Dashboard */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-8 md:p-12">
            <CostDashboard />
          </div>
        </div>
      </div>
      </div>

      {/* Post Detail Modal */}
      {selectedPost && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedPost(null)}
        >
          <div 
            className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-semibold text-gray-900">Post Details</h3>
                <div className="flex gap-2 mt-2">
                  <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-md text-xs font-medium">
                    {selectedPost.target_type}
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-md text-xs font-medium">
                    {selectedPost.lifecycle}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedPost(null)}
                className="w-10 h-10 rounded-full hover:bg-gray-100 flex items-center justify-center transition-colors"
              >
                <span className="text-2xl text-gray-400">×</span>
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Image */}
              {selectedPost.image_url && (
                <div className="rounded-xl overflow-hidden border border-gray-200">
                  <img
                    src={resolveMediaUrl(selectedPost.image_url)}
                    alt={selectedPost.image_description || "Post image"}
                    className="w-full h-auto"
                    loading="lazy"
                  />
                  {selectedPost.image_description && (
                    <div className="p-4 bg-gray-50 border-t border-gray-200">
                      <p className="text-sm text-gray-700">
                        <strong className="font-semibold">Image:</strong> {selectedPost.image_description}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Content */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3">Content</h4>
                <div className="whitespace-pre-wrap text-gray-800 leading-relaxed bg-gray-50 p-6 rounded-lg border border-gray-200">
                  {selectedPost.content || selectedPost.commentary}
                </div>
              </div>

              {/* Hashtags */}
              {selectedPost.hashtags && selectedPost.hashtags.length > 0 && (
                <div>
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">Hashtags</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedPost.hashtags.map((tag, i) => (
                      <span
                        key={i}
                        className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md text-sm font-medium border border-blue-200"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    const text = selectedPost.content || selectedPost.commentary || "";
                    navigator.clipboard.writeText(text);
                  }}
                  className="px-6 py-3 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg font-medium text-sm border border-gray-200 hover:border-gray-300 transition-all duration-200"
                >
                  📋 Copy Content
                </button>
                <button
                  onClick={() => {
                    const text = selectedPost.content || selectedPost.commentary || "";
                    const hashtags = selectedPost.hashtags?.map(t => `#${t}`).join(" ") || "";
                    navigator.clipboard.writeText(`${text}\n\n${hashtags}`);
                  }}
                  className="px-6 py-3 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg font-medium text-sm border border-blue-200 hover:border-blue-300 transition-all duration-200"
                >
                  📋 Copy with Hashtags
                </button>
                {selectedPost.image_url && (
                  <button
                    onClick={() => window.open(resolveMediaUrl(selectedPost.image_url), "_blank")}
                    className="col-span-2 px-6 py-3 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-lg font-medium text-sm border border-purple-200 hover:border-purple-300 transition-all duration-200"
                  >
                    🖼️ Open Full Image
                  </button>
                )}
              </div>

              {/* Close Button */}
              <button
                onClick={() => setSelectedPost(null)}
                className="w-full px-6 py-3 bg-white hover:bg-gray-50 text-gray-900 rounded-lg font-medium text-sm border-2 border-gray-300 hover:border-gray-400 transition-all duration-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}