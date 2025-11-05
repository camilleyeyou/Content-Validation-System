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
      <div className="p-8">
        <div className="text-center py-16">
          <div className="relative inline-block mb-6">
            <div className="w-24 h-24 border-8 border-purple-200 border-t-purple-600 rounded-full animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl">✨</span>
            </div>
          </div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">Generating Your Perfect Post...</h3>
          <p className="text-gray-600 mb-4">Our AI is crafting content tailored to your exact specifications</p>
          <div className="max-w-md mx-auto space-y-2 text-sm text-gray-500">
            <p>✓ Applying brand voice settings</p>
            <p>✓ Weaving in inspiration sources</p>
            <p>✓ Validating with personas</p>
            <p>✓ Generating professional image with CTA</p>
          </div>
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="p-8">
        <div className="text-center py-16">
          <div className="text-6xl mb-4">😕</div>
          <h3 className="text-xl font-bold text-gray-900 mb-2">No Post Generated</h3>
          <p className="text-gray-600 mb-6">Something went wrong during generation</p>
          <button
            onClick={generatePost}
            className="px-8 py-3 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Your Generated Post</h2>
        <p className="text-gray-600">
          Review, copy, and publish your AI-crafted LinkedIn content
        </p>
      </div>

      {/* Validation Status */}
      {validation && (
        <div className={`mb-6 p-4 rounded-xl border-2 ${
          validation.approved
            ? "bg-green-50 border-green-300"
            : "bg-yellow-50 border-yellow-300"
        }`}>
          <div className="flex items-center gap-3">
            <span className="text-2xl">{validation.approved ? "✅" : "⚠️"}</span>
            <div>
              <div className="font-bold text-gray-900">
                {validation.approved ? "Validated & Approved" : "Needs Review"}
              </div>
              <div className="text-sm text-gray-700">
                {validation.approved
                  ? "This post passed all validation criteria"
                  : validation.feedback || "Some validators had concerns"}
              </div>
            </div>
          </div>

          {/* Validator Scores */}
          {validation.validator_scores && validation.validator_scores.length > 0 && (
            <div className="mt-4 grid grid-cols-3 gap-3">
              {validation.validator_scores.map((score: any, idx: number) => (
                <div key={idx} className="bg-white p-3 rounded-lg border border-gray-200">
                  <div className="text-xs font-semibold text-gray-600 mb-1">{score.agent}</div>
                  <div className="flex items-center gap-2">
                    <span className={`text-lg ${score.approved ? "text-green-600" : "text-red-600"}`}>
                      {score.approved ? "✓" : "✗"}
                    </span>
                    <span className="font-bold text-gray-900">{score.score.toFixed(1)}/10</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        {/* Post Content */}
        <div className="bg-white border-2 border-gray-200 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <h3 className="font-bold text-gray-900">Content</h3>
          </div>
          <div className="p-6">
            <div className="whitespace-pre-wrap text-gray-900 leading-relaxed mb-6">
              {post.content}
            </div>

            {post.hashtags && post.hashtags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {post.hashtags.map((tag: string, idx: number) => (
                  <span key={idx} className="text-sm bg-blue-100 text-blue-800 px-3 py-1 rounded-full font-semibold">
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {post.cultural_reference && (
              <div className="text-sm text-gray-600 bg-purple-50 p-3 rounded-lg border border-purple-200">
                <strong>Cultural Reference:</strong> {post.cultural_reference.reference}
              </div>
            )}
          </div>
        </div>

        {/* Image Preview */}
        <div className="bg-white border-2 border-gray-200 rounded-xl overflow-hidden">
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <h3 className="font-bold text-gray-900">Generated Image</h3>
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
                <div className="p-4 bg-gray-50 border-t border-gray-200">
                  <div className="text-xs text-gray-600">
                    <strong>Image:</strong> {post.image_description}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-gray-400">
              <div className="text-6xl mb-4">🖼️</div>
              <p>No image generated</p>
            </div>
          )}
        </div>
      </div>

      {/* Metadata */}
      {metadata && (
        <div className="mb-8 p-6 bg-gray-50 rounded-xl border border-gray-200">
          <h4 className="font-bold text-gray-900 mb-3">Generation Details</h4>
          <div className="grid md:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-600 mb-1">Generation Time</div>
              <div className="font-semibold text-gray-900">{metadata.generation_time_seconds}s</div>
            </div>
            <div>
              <div className="text-gray-600 mb-1">Inspiration Sources</div>
              <div className="font-semibold text-gray-900">{metadata.inspiration_sources?.length || 0}</div>
            </div>
            <div>
              <div className="text-gray-600 mb-1">Length Target</div>
              <div className="font-semibold text-gray-900">{metadata.length}</div>
            </div>
            <div>
              <div className="text-gray-600 mb-1">Persona Validated</div>
              <div className="font-semibold text-gray-900">{metadata.persona_validated ? "Yes" : "No"}</div>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="space-y-4">
        <div className="flex gap-3">
          <button
            onClick={() => copyToClipboard(post.content)}
            className="flex-1 px-6 py-4 bg-gray-900 text-white rounded-xl font-bold hover:bg-gray-800 transition-all flex items-center justify-center gap-2"
          >
            <span className="text-xl">📋</span>
            Copy Content
          </button>

          <button
            onClick={() => copyToClipboard(`${post.content}\n\n${post.hashtags?.map((t: string) => `#${t}`).join(" ") || ""}`)}
            className="flex-1 px-6 py-4 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700 transition-all flex items-center justify-center gap-2"
          >
            <span className="text-xl">📋</span>
            Copy with Hashtags
          </button>

          {post.image_url && (
            <button
              onClick={() => window.open(resolveImageUrl(post.image_url), "_blank")}
              className="flex-1 px-6 py-4 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 transition-all flex items-center justify-center gap-2"
            >
              <span className="text-xl">🖼️</span>
              Open Image
            </button>
          )}
        </div>

        {copySuccess && (
          <div className="text-center text-green-600 font-semibold">
            {copySuccess}
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="mt-8 pt-6 border-t border-gray-200 flex items-center justify-between">
        <button
          onClick={onBack}
          className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50 transition-all"
        >
          ← Back to Persona
        </button>

        <div className="flex gap-3">
          <button
            onClick={() => {
              setState(prev => ({ ...prev, generatedPost: undefined, currentStep: 1 }));
            }}
            className="px-6 py-3 border-2 border-purple-600 text-purple-700 rounded-xl font-bold hover:bg-purple-50 transition-all"
          >
            🔄 Create Another
          </button>

          <a
            href="/"
            className="px-8 py-3 bg-gradient-to-r from-green-600 to-blue-600 text-white rounded-xl font-bold hover:from-green-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl inline-flex items-center gap-2"
          >
            <span className="text-xl">✅</span>
            Done
          </a>
        </div>
      </div>
    </div>
  );
}