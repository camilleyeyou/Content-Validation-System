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

        {/* Campaign Examples Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-8 md:p-12">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                Inspiration Gallery
              </h2>
              <p className="text-gray-600">
                See what our AI-powered system can create for you
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* The Zeitgeist Post */}
              <div className="border border-gray-200 rounded-xl p-6 bg-gradient-to-br from-gray-50 to-white hover:shadow-md transition-all duration-300">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-purple-600 mb-1">The Zeitgeist Post</h3>
                    <p className="text-sm font-medium text-gray-500">News-Hook Driven</p>
                  </div>
                  <div className="text-3xl">📰</div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-200 mb-4 min-h-[180px]">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                    Everyone's talking about the new AI regulations, but they're missing the point.{'\n\n'}
                    It's not about restriction; it's about intention. This is a moment to pause, reflect on our 'why', and build more mindful tech. That's the real ritual.{'\n\n'}
                    #AI #TechEthics #MindfulProductivity
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-md font-medium">
                    60% Formal Tone
                  </span>
                  <span className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md font-medium">
                    Medium Length
                  </span>
                  <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-md font-medium">
                    News Inspired
                  </span>
                </div>
              </div>

              {/* The Humanist Post */}
              <div className="border border-gray-200 rounded-xl p-6 bg-gradient-to-br from-gray-50 to-white hover:shadow-md transition-all duration-300">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-purple-600 mb-1">The Humanist Post</h3>
                    <p className="text-sm font-medium text-gray-500">Poetic & Evocative</p>
                  </div>
                  <div className="text-3xl">✒️</div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-200 mb-4 min-h-[180px]">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                    The space between tasks is not emptiness to be filled, but a canvas for intention.{'\n\n'}
                    A simple pause, a mindful breath. This is where the work truly happens.{'\n\n'}
                    It's not about doing more; it's about being more present in what you do. Stop. Breathe. Balm.{'\n\n'}
                    #Productivity #Wellness #WorkLifeBalance
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-md font-medium">
                    40% Formal Tone
                  </span>
                  <span className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md font-medium">
                    Short Length
                  </span>
                  <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-md font-medium">
                    Mary Oliver Inspired
                  </span>
                </div>
              </div>

              {/* The Sage Post */}
              <div className="border border-gray-200 rounded-xl p-6 bg-gradient-to-br from-gray-50 to-white hover:shadow-md transition-all duration-300">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-purple-600 mb-1">The Sage Post</h3>
                    <p className="text-sm font-medium text-gray-500">Philosophical & Insightful</p>
                  </div>
                  <div className="text-3xl">🏛️</div>
                </div>

                <div className="bg-white p-4 rounded-lg border border-gray-200 mb-4 min-h-[180px]">
                  <p className="text-sm text-gray-800 whitespace-pre-wrap leading-relaxed">
                    Seneca wrote, 'It is not that we have a short time to live, but that we waste a lot of it.'{'\n\n'}
                    In our rush to optimize every minute, have we forgotten the value of the minute itself? The greatest productivity hack isn't a tool; it's a philosophy. A deliberate intention to reclaim your focus.{'\n\n'}
                    #Stoicism #Productivity #DeepWork
                  </p>
                </div>

                <div className="flex flex-wrap gap-2 text-xs">
                  <span className="px-3 py-1.5 bg-purple-100 text-purple-700 rounded-md font-medium">
                    75% Formal Tone
                  </span>
                  <span className="px-3 py-1.5 bg-blue-100 text-blue-700 rounded-md font-medium">
                    Medium Length
                  </span>
                  <span className="px-3 py-1.5 bg-green-100 text-green-700 rounded-md font-medium">
                    Seneca Inspired
                  </span>
                </div>
              </div>
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
          </div>
        </div>

        {/* Cost Dashboard */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-8 md:p-12">
            <CostDashboard />
          </div>
        </div>
      </div>
    </main>
  );
}