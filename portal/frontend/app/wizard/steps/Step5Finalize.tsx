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
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-16 text-center">
            <div className="relative inline-block mb-8">
              <div 
                className="w-24 h-24 border-8 border-purple-200 border-t-purple-600 rounded-full animate-spin"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-4xl">✨</span>
              </div>
            </div>
            <h3 className="text-2xl md:text-3xl font-semibold text-gray-900 mb-3">
              Generating Your Perfect Post...
            </h3>
            <p className="text-gray-600 mb-8 leading-relaxed">
              Our AI is crafting content tailored to your exact specifications
            </p>
            <div className="max-w-md mx-auto space-y-3 text-sm text-gray-600">
              <p className="flex items-center justify-center gap-2">
                <span className="text-purple-600">✓</span> Applying brand voice settings
              </p>
              <p className="flex items-center justify-center gap-2">
                <span className="text-purple-600">✓</span> Weaving in inspiration sources
              </p>
              <p className="flex items-center justify-center gap-2">
                <span className="text-purple-600">✓</span> Validating with personas
              </p>
              <p className="flex items-center justify-center gap-2">
                <span className="text-purple-600">✓</span> Generating professional image with CTA
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-16 text-center">
            <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6 border border-gray-200">
              <span className="text-5xl">😕</span>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-3">No Post Generated</h3>
            <p className="text-gray-600 mb-8 leading-relaxed">Something went wrong during generation</p>
            <button
              onClick={generatePost}
              className="px-12 py-4 text-white rounded-lg font-medium tracking-wider uppercase text-sm shadow-lg hover:shadow-xl transition-all duration-300"
              style={{
                background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
              }}
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <h2 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-3">
            Your Generated Post
          </h2>
          <p className="text-sm md:text-base text-gray-600 leading-relaxed">
            Review, copy, and publish your AI-crafted LinkedIn content
          </p>
        </div>
      </div>

      {/* Validation Status Card */}
      {validation && (
        <div className={`bg-white rounded-xl shadow-sm border overflow-hidden ${
          validation.approved
            ? "border-green-300"
            : "border-yellow-300"
        }`}>
          <div className="p-8 md:p-10">
            <div className="flex items-start gap-4 mb-6">
              <span className="text-3xl">{validation.approved ? "✅" : "⚠️"}</span>
              <div className="flex-1">
                <div className="text-gray-900 text-xl mb-2 font-semibold">
                  {validation.approved ? "Validated & Approved" : "Needs Review"}
                </div>
                <div className="text-sm text-gray-600 leading-relaxed">
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
                    className="bg-gray-50 p-5 rounded-lg border border-gray-200 hover:border-purple-300 transition-all duration-300"
                  >
                    <div className="text-xs font-medium text-gray-600 mb-2 uppercase tracking-wider">
                      {score.agent}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-xl ${score.approved ? "text-green-500" : "text-red-500"}`}>
                        {score.approved ? "✓" : "✗"}
                      </span>
                      <span className="text-gray-900 text-lg font-semibold">
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

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Post Content Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-6 md:p-8 border-b border-gray-200">
            <h3 className="text-gray-900 text-xl font-semibold">Content</h3>
          </div>
          <div className="p-6 md:p-8">
            <div className="whitespace-pre-wrap text-gray-800 leading-relaxed mb-6">
              {post.content}
            </div>

            {post.hashtags && post.hashtags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {post.hashtags.map((tag: string, idx: number) => (
                  <span 
                    key={idx} 
                    className="text-xs bg-blue-100 text-blue-700 px-3 py-1.5 rounded-lg font-medium uppercase tracking-wider border border-blue-200"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {post.cultural_reference && (
              <div className="text-sm text-gray-700 bg-purple-50 p-4 rounded-lg border border-purple-200 leading-relaxed">
                <strong className="text-purple-700 font-semibold">Cultural Reference:</strong> {post.cultural_reference.reference}
              </div>
            )}
          </div>
        </div>

        {/* Image Preview Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-6 md:p-8 border-b border-gray-200">
            <h3 className="text-gray-900 text-xl font-semibold">Generated Image</h3>
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
                <div className="p-5 bg-gray-50 border-t border-gray-200">
                  <div className="text-xs text-gray-700 leading-relaxed">
                    <strong className="text-gray-900 font-semibold">Image:</strong> {post.image_description}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-16 text-center text-gray-500">
              <div className="w-20 h-20 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4 border border-gray-200">
                <span className="text-4xl">🖼️</span>
              </div>
              <p>No image generated</p>
            </div>
          )}
        </div>
      </div>

      {/* Metadata Card */}
      {metadata && (
        <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-xl border border-gray-200 overflow-hidden">
          <div className="p-8 md:p-10">
            <h4 className="text-gray-900 text-xl mb-6 font-semibold flex items-center gap-3">
              <span className="text-2xl">✦</span>
              Generation Details
            </h4>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 text-sm">
              <div>
                <div className="text-gray-600 mb-2 uppercase tracking-wider text-xs font-medium">Generation Time</div>
                <div className="text-purple-700 text-xl font-semibold">{metadata.generation_time_seconds}s</div>
              </div>
              <div>
                <div className="text-gray-600 mb-2 uppercase tracking-wider text-xs font-medium">Inspiration Sources</div>
                <div className="text-purple-700 text-xl font-semibold">{metadata.inspiration_sources?.length || 0}</div>
              </div>
              <div>
                <div className="text-gray-600 mb-2 uppercase tracking-wider text-xs font-medium">Length Target</div>
                <div className="text-purple-700 text-xl font-semibold">{metadata.length}</div>
              </div>
              <div>
                <div className="text-gray-600 mb-2 uppercase tracking-wider text-xs font-medium">Persona Validated</div>
                <div className="text-purple-700 text-xl font-semibold">{metadata.persona_validated ? "Yes" : "No"}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <div className="grid sm:grid-cols-3 gap-4 mb-6">
            <button
              onClick={() => copyToClipboard(post.content)}
              className="px-6 py-4 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg font-medium tracking-wider uppercase text-xs border border-gray-200 hover:border-purple-300 transition-all duration-300 flex items-center justify-center gap-2"
            >
              <span className="text-lg">📋</span>
              Copy Content
            </button>

            <button
              onClick={() => copyToClipboard(`${post.content}\n\n${post.hashtags?.map((t: string) => `#${t}`).join(" ") || ""}`)}
              className="px-6 py-4 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg font-medium tracking-wider uppercase text-xs border border-blue-200 hover:border-blue-300 transition-all duration-300 flex items-center justify-center gap-2"
            >
              <span className="text-lg">📋</span>
              Copy with Hashtags
            </button>

            {post.image_url && (
              <button
                onClick={() => window.open(resolveImageUrl(post.image_url), "_blank")}
                className="px-6 py-4 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-lg font-medium tracking-wider uppercase text-xs border border-purple-200 hover:border-purple-300 transition-all duration-300 flex items-center justify-center gap-2"
              >
                <span className="text-lg">🖼️</span>
                Open Image
              </button>
            )}
          </div>

          {copySuccess && (
            <div className="text-center text-green-600 font-medium text-sm">
              {copySuccess}
            </div>
          )}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="px-8 py-4 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg font-medium tracking-wider uppercase text-sm border border-gray-200 hover:border-gray-300 transition-all duration-300"
        >
          ← Back to Persona
        </button>

        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => {
              setState(prev => ({ ...prev, generatedPost: undefined, currentStep: 1 }));
            }}
            className="px-8 py-4 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg font-medium tracking-wider uppercase text-sm border border-purple-300 hover:border-purple-400 transition-all duration-300 flex items-center justify-center gap-2"
          >
            <span className="text-lg">🔄</span>
            Create Another
          </button>

          <a
            href="/"
            className="px-12 py-4 text-white rounded-lg font-medium tracking-wider uppercase text-sm shadow-lg hover:shadow-xl transition-all duration-300 inline-flex items-center justify-center gap-2"
            style={{
              background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
            }}
          >
            <span className="text-lg">✅</span>
            Done
          </a>
        </div>
      </div>
    </div>
  );
}