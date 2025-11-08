// portal/frontend/app/wizard/steps/Step5Finalize.tsx
"use client";
import { useState, useEffect } from "react";
import { WizardState } from "../page";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8001";

// Helper function to ensure image URLs point to backend
function resolveImageUrl(url: string | undefined | null): string | undefined {
  if (!url) return undefined;
  
  // If already absolute URL, return as-is
  if (url.startsWith("http://") || url.startsWith("https://")) {
    return url;
  }
  
  // If relative path starting with /images/, prepend API_BASE
  if (url.startsWith("/images/")) {
    return `${API_BASE}${url}`;
  }
  
  // If just a filename or other relative path, assume it's under /images/
  if (!url.includes("/")) {
    return `${API_BASE}/images/${url}`;
  }
  
  return url;
}

type Props = {
  state: WizardState;
  setState: React.Dispatch<React.SetStateAction<WizardState>>;
  onBack: () => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
};

export default function Step5Finalize({ state, setState, onBack, loading, setLoading, setError }: Props) {
  const [copySuccess, setCopySuccess] = useState("");

  // Auto-generate on mount if not already generated
  useEffect(() => {
    if (!state.generatedPost && !loading) {
      generatePost();
    }
  }, []);

  async function generatePost() {
    setLoading(true);
    setError("");
    setCopySuccess("");

    try {
      // Build request payload
      const payload = {
        brand_settings: {
          tone_slider: state.brandSettings.tone,
          pithiness_slider: state.brandSettings.pithiness,
          jargon_slider: state.brandSettings.jargon,
          custom_additions: state.brandSettings.custom
        },
        inspiration_selections: state.inspirationSelections.map(sel => ({
          type: sel.type,
          selected_id: sel.selected_id
        })),
        style_preferences: {
          length: state.length,
          style_flags: state.styleFlags
        },
        buyer_persona: state.buyerPersona || null
      };

      const response = await fetch(`${API_BASE}/api/wizard/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!data.ok) {
        throw new Error(data.detail || "Generation failed");
      }

      setState(prev => ({ ...prev, generatedPost: data }));
    } catch (e: any) {
      setError(e.message || "Failed to generate post");
    } finally {
      setLoading(false);
    }
  }

  async function copyToClipboard(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopySuccess("✓ Copied to clipboard!");
      setTimeout(() => setCopySuccess(""), 2000);
    } catch (e) {
      setCopySuccess("❌ Failed to copy");
    }
  }

  const post = state.generatedPost?.post;
  const validation = state.generatedPost?.validation;
  const metadata = state.generatedPost?.metadata;

  if (loading) {
    return (
      <div className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
        <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
            <div className="p-16 text-center">
              <div className="relative inline-block mb-8">
                <div className="w-24 h-24 border-8 border-[#d4af37]/20 border-t-[#d4af37] rounded-full animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-4xl">✨</span>
                </div>
              </div>
              <h3 className="text-2xl md:text-3xl font-serif font-light text-white mb-3 tracking-wide">
                Generating Your Perfect Post...
              </h3>
              <p className="text-gray-400 font-light mb-8 leading-relaxed">
                Our AI is crafting content tailored to your exact specifications
              </p>
              <div className="max-w-md mx-auto space-y-3 text-sm text-gray-500 font-light">
                <p className="flex items-center justify-center gap-2">
                  <span className="text-[#d4af37]">✓</span> Applying brand voice settings
                </p>
                <p className="flex items-center justify-center gap-2">
                  <span className="text-[#d4af37]">✓</span> Weaving in inspiration sources
                </p>
                <p className="flex items-center justify-center gap-2">
                  <span className="text-[#d4af37]">✓</span> Validating with personas
                </p>
                <p className="flex items-center justify-center gap-2">
                  <span className="text-[#d4af37]">✓</span> Generating professional image with CTA
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
        <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-white/10 shadow-2xl overflow-hidden">
            <div className="p-16 text-center">
              <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-white/10">
                <span className="text-5xl">😕</span>
              </div>
              <h3 className="text-2xl font-serif font-light text-white mb-3 tracking-wide">No Post Generated</h3>
              <p className="text-gray-400 font-light mb-8 leading-relaxed">Something went wrong during generation</p>
              <button
                onClick={generatePost}
                className="px-12 py-4 bg-gradient-to-br from-[#d4af37] to-[#b8941f] text-black rounded-sm font-light tracking-wider uppercase text-sm hover:shadow-2xl hover:shadow-[#d4af37]/20 transition-all duration-500"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
      <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
        {/* Header Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h2 className="text-3xl md:text-4xl font-serif font-light text-white mb-3 tracking-wide">
              Your Generated Post
            </h2>
            <p className="text-sm md:text-base text-gray-400 font-light leading-relaxed">
              Review, copy, and publish your AI-crafted LinkedIn content
            </p>
          </div>
        </div>

        {/* Validation Status Card */}
        {validation && (
          <div className={`bg-black/40 backdrop-blur-sm rounded-sm border shadow-2xl overflow-hidden mb-8 ${
            validation.approved
              ? "border-emerald-500/30"
              : "border-yellow-500/30"
          }`}>
            <div className="p-8 md:p-10">
              <div className="flex items-start gap-4 mb-6">
                <span className="text-3xl">{validation.approved ? "✅" : "⚠️"}</span>
                <div className="flex-1">
                  <div className="font-serif text-white text-xl mb-2 font-light tracking-wide">
                    {validation.approved ? "Validated & Approved" : "Needs Review"}
                  </div>
                  <div className="text-sm text-gray-400 font-light leading-relaxed">
                    {validation.approved
                      ? "This post passed all validation criteria"
                      : validation.feedback || "Some validators had concerns"}
                  </div>
                </div>
              </div>

              {/* Validator Scores */}
              {validation.validator_scores && validation.validator_scores.length > 0 && (
                <div className="grid sm:grid-cols-3 gap-4">
                  {validation.validator_scores.map((score: any, idx: number) => (
                    <div 
                      key={idx} 
                      className="bg-black/60 p-5 rounded-sm border border-white/10 hover:border-[#d4af37]/30 transition-all duration-300"
                    >
                      <div className="text-xs font-light text-gray-500 mb-2 uppercase tracking-wider">
                        {score.agent}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-xl ${score.approved ? "text-emerald-400" : "text-red-400"}`}>
                          {score.approved ? "✓" : "✗"}
                        </span>
                        <span className="font-serif text-white text-lg font-light">
                          {score.score.toFixed(1)}<span className="text-gray-500">/10</span>
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* Post Content Card */}
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
            <div className="p-6 md:p-8 border-b border-white/10">
              <h3 className="font-serif text-white text-xl font-light tracking-wide">Content</h3>
            </div>
            <div className="p-6 md:p-8">
              <div className="whitespace-pre-wrap text-gray-200 leading-relaxed mb-6 font-light">
                {post.content}
              </div>

              {post.hashtags && post.hashtags.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-6">
                  {post.hashtags.map((tag: string, idx: number) => (
                    <span 
                      key={idx} 
                      className="text-xs bg-blue-500/10 text-blue-300 px-3 py-1.5 rounded-sm font-light uppercase tracking-wider border border-blue-500/30"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}

              {post.cultural_reference && (
                <div className="text-sm text-gray-400 bg-purple-500/10 p-4 rounded-sm border border-purple-500/30 font-light leading-relaxed">
                  <strong className="text-purple-300 font-normal">Cultural Reference:</strong> {post.cultural_reference.reference}
                </div>
              )}
            </div>
          </div>

          {/* Image Preview Card */}
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
            <div className="p-6 md:p-8 border-b border-white/10">
              <h3 className="font-serif text-white text-xl font-light tracking-wide">Generated Image</h3>
            </div>
            {post.image_url ? (
              <div>
                <div className="relative w-full" style={{ paddingTop: "56.25%" }}>
                  <img
                    src={resolveImageUrl(post.image_url)}
                    alt={post.image_description || "Generated post image"}
                    className="absolute inset-0 w-full h-full object-cover"
                    loading="lazy"
                  />
                </div>
                {post.image_description && (
                  <div className="p-5 bg-black/60 border-t border-white/10">
                    <div className="text-xs text-gray-400 font-light leading-relaxed">
                      <strong className="text-gray-300 font-normal">Image:</strong> {post.image_description}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-16 text-center text-gray-500">
                <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 border border-white/10">
                  <span className="text-4xl">🖼️</span>
                </div>
                <p className="font-light">No image generated</p>
              </div>
            )}
          </div>
        </div>

        {/* Metadata Card */}
        {metadata && (
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
            <div className="p-8 md:p-10">
              <h4 className="font-serif text-white text-xl mb-6 font-light tracking-wide flex items-center gap-3">
                <span className="text-2xl">✦</span>
                Generation Details
              </h4>
              <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 text-sm">
                <div>
                  <div className="text-gray-500 mb-2 uppercase tracking-wider text-xs font-light">Generation Time</div>
                  <div className="font-serif text-[#d4af37] text-xl font-light">{metadata.generation_time_seconds}s</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-2 uppercase tracking-wider text-xs font-light">Inspiration Sources</div>
                  <div className="font-serif text-[#d4af37] text-xl font-light">{metadata.inspiration_sources?.length || 0}</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-2 uppercase tracking-wider text-xs font-light">Length Target</div>
                  <div className="font-serif text-[#d4af37] text-xl font-light">{metadata.length}</div>
                </div>
                <div>
                  <div className="text-gray-500 mb-2 uppercase tracking-wider text-xs font-light">Persona Validated</div>
                  <div className="font-serif text-[#d4af37] text-xl font-light">{metadata.persona_validated ? "Yes" : "No"}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <div className="grid sm:grid-cols-3 gap-4 mb-6">
              <button
                onClick={() => copyToClipboard(post.content)}
                className="px-6 py-4 bg-white/5 hover:bg-white/10 text-white rounded-sm font-light tracking-wider uppercase text-xs border border-white/10 hover:border-[#d4af37]/30 transition-all duration-300 flex items-center justify-center gap-2"
              >
                <span className="text-lg">📋</span>
                Copy Content
              </button>

              <button
                onClick={() => copyToClipboard(`${post.content}\n\n${post.hashtags?.map((t: string) => `#${t}`).join(" ") || ""}`)}
                className="px-6 py-4 bg-blue-500/10 hover:bg-blue-500/20 text-blue-300 rounded-sm font-light tracking-wider uppercase text-xs border border-blue-500/30 hover:border-blue-500/50 transition-all duration-300 flex items-center justify-center gap-2"
              >
                <span className="text-lg">📋</span>
                Copy with Hashtags
              </button>

              {post.image_url && (
                <button
                  onClick={() => window.open(resolveImageUrl(post.image_url), "_blank")}
                  className="px-6 py-4 bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 rounded-sm font-light tracking-wider uppercase text-xs border border-purple-500/30 hover:border-purple-500/50 transition-all duration-300 flex items-center justify-center gap-2"
                >
                  <span className="text-lg">🖼️</span>
                  Open Image
                </button>
              )}
            </div>

            {copySuccess && (
              <div className="text-center text-emerald-400 font-light text-sm">
                {copySuccess}
              </div>
            )}
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
          <button
            onClick={onBack}
            className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white rounded-sm font-light tracking-wider uppercase text-sm border border-white/10 hover:border-white/20 transition-all duration-300"
          >
            ← Back to Persona
          </button>

          <div className="flex flex-col sm:flex-row gap-4">
            <button
              onClick={() => {
                setState(prev => ({ ...prev, generatedPost: undefined, currentStep: 1 }));
              }}
              className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white rounded-sm font-light tracking-wider uppercase text-sm border border-[#d4af37]/30 hover:border-[#d4af37]/50 transition-all duration-300 flex items-center justify-center gap-2"
            >
              <span className="text-lg">🔄</span>
              Create Another
            </button>

            <a
              href="/"
              className="px-12 py-4 bg-gradient-to-br from-[#d4af37] to-[#b8941f] text-black rounded-sm font-light tracking-wider uppercase text-sm hover:shadow-2xl hover:shadow-[#d4af37]/20 transition-all duration-500 inline-flex items-center justify-center gap-2"
            >
              <span className="text-lg">✅</span>
              Done
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}