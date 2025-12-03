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
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [savedPostId, setSavedPostId] = useState<string | null>(null);
  const [expandedValidators, setExpandedValidators] = useState<Set<number>>(new Set([0, 1, 2])); // All expanded by default

  // Auto-generate on mount if not already generated
  useEffect(() => {
    if (!state.generatedPost && !loading) {
      generatePost();
    }
  }, []);

  // Auto-save after generation
  useEffect(() => {
    if (state.generatedPost?.post && saveStatus === "idle") {
      savePostToDashboard();
    }
  }, [state.generatedPost]);

  async function generatePost() {
    setLoading(true);
    setError("");
    setCopySuccess("");
    setSaveStatus("idle");

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

  async function savePostToDashboard() {
    const post = state.generatedPost?.post;
    if (!post) return;

    setSaveStatus("saving");

    try {
      // Build the payload with only the fields the backend expects
      // Backend requires commentary, but wizard generates content
      // Use content for both fields
      const payload: any = {
        target_type: post.target_type || "MEMBER",
        commentary: post.content || "", // Backend requires this field
        content: post.content || "",
        hashtags: post.hashtags || []
      };

      // Add optional fields only if they exist
      if (post.image_url) {
        payload.image_url = post.image_url;
      }
      if (post.image_description) {
        payload.image_description = post.image_description;
      }
      if (post.image_prompt) {
        payload.image_prompt = post.image_prompt;
      }

      console.log("Saving post with payload:", payload);

      // 1. Save the post
      const saveResponse = await fetch(`${API_BASE}/api/posts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!saveResponse.ok) {
        const errorText = await saveResponse.text();
        console.error("Save failed:", saveResponse.status, errorText);
        throw new Error(`Save failed: ${saveResponse.status} - ${errorText}`);
      }

      const saveData = await saveResponse.json();
      console.log("Save response:", saveData);
      
      if (!saveData.ok) {
        throw new Error("Failed to save post");
      }

      const postId = saveData.post?.id;
      setSavedPostId(postId);

      // 2. Approve the post (backend saves as draft by default)
      if (postId) {
        const approveResponse = await fetch(`${API_BASE}/api/posts/${postId}/approve`, {
          method: "POST"
        });
        
        if (approveResponse.ok) {
          console.log("Post approved successfully");
        }

        // 3. Refresh showcase
        const refreshResponse = await fetch(`${API_BASE}/api/showcase/refresh`, {
          method: "POST"
        });
        
        if (refreshResponse.ok) {
          console.log("Showcase refreshed successfully");
        }
      }

      setSaveStatus("saved");
    } catch (e: any) {
      console.error("Save error:", e);
      setSaveStatus("error");
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

  function toggleValidator(idx: number) {
    setExpandedValidators(prev => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  }

  // Helper to get validator persona details
  function getValidatorInfo(agentName: string): { title: string; emoji: string; color: string } {
    const name = agentName.toLowerCase();
    if (name.includes("sarah") || name.includes("chen") || name.includes("customer")) {
      return { title: "Customer Perspective", emoji: "👩‍💼", color: "purple" };
    }
    if (name.includes("marcus") || name.includes("williams") || name.includes("business")) {
      return { title: "Business Strategy", emoji: "👨‍💼", color: "blue" };
    }
    if (name.includes("jordan") || name.includes("park") || name.includes("social")) {
      return { title: "Social Engagement", emoji: "🎯", color: "teal" };
    }
    return { title: "Validator", emoji: "🤖", color: "gray" };
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
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-3">
                Your Generated Post
              </h2>
              <p className="text-sm md:text-base text-gray-600 leading-relaxed">
                Review, copy, and publish your AI-crafted LinkedIn content
              </p>
            </div>
            
            {/* Save Status Badge */}
            {saveStatus === "saving" && (
              <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 text-blue-700 rounded-lg text-sm font-medium border border-blue-200">
                <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                Saving...
              </div>
            )}
            {saveStatus === "saved" && (
              <div className="flex items-center gap-2 px-4 py-2 bg-green-50 text-green-700 rounded-lg text-sm font-medium border border-green-200">
                <span className="text-lg">✅</span>
                Saved to Dashboard
              </div>
            )}
            {saveStatus === "error" && (
              <div className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-700 rounded-lg text-sm font-medium border border-red-200">
                <span className="text-lg">❌</span>
                Save Failed
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Validation Status Card - Enhanced with Comments */}
      {validation && (
        <div className={`bg-white rounded-xl shadow-sm border overflow-hidden ${
          validation.approved
            ? "border-green-300"
            : "border-yellow-300"
        }`}>
          <div className="p-8 md:p-10">
            {/* Overall Status Header */}
            <div className="flex items-start gap-4 mb-6">
              <span className="text-3xl">{validation.approved ? "✅" : "⚠️"}</span>
              <div className="flex-1">
                <div className="text-gray-900 text-xl mb-2 font-semibold">
                  {validation.approved ? "Validated & Approved" : "Needs Review"}
                </div>
                <div className="text-sm text-gray-600 leading-relaxed">
                  {validation.approved
                    ? "This post passed all validation criteria from our expert panel"
                    : validation.feedback || "Some validators had concerns - see their feedback below"}
                </div>
              </div>
            </div>

            {/* Validator Feedback Cards - Enhanced with Comments */}
            {validation.validator_scores && validation.validator_scores.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">
                    Expert Validator Feedback
                  </h4>
                  <button
                    onClick={() => {
                      if (expandedValidators.size === validation.validator_scores.length) {
                        setExpandedValidators(new Set());
                      } else {
                        setExpandedValidators(new Set(validation.validator_scores.map((_: any, i: number) => i)));
                      }
                    }}
                    className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                  >
                    {expandedValidators.size === validation.validator_scores.length ? "Collapse All" : "Expand All"}
                  </button>
                </div>

                {validation.validator_scores.map((score: any, idx: number) => {
                  const validatorInfo = getValidatorInfo(score.agent);
                  const isExpanded = expandedValidators.has(idx);
                  
                  return (
                    <div 
                      key={idx} 
                      className={`rounded-xl border transition-all duration-300 overflow-hidden ${
                        score.approved 
                          ? "border-green-200 bg-gradient-to-br from-green-50/50 to-white" 
                          : "border-amber-200 bg-gradient-to-br from-amber-50/50 to-white"
                      }`}
                    >
                      {/* Validator Header - Always Visible */}
                      <button
                        onClick={() => toggleValidator(idx)}
                        className="w-full p-5 flex items-center justify-between hover:bg-gray-50/50 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl ${
                            score.approved ? "bg-green-100" : "bg-amber-100"
                          }`}>
                            {validatorInfo.emoji}
                          </div>
                          <div className="text-left">
                            <div className="font-semibold text-gray-900 text-lg">
                              {score.agent.split('_').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                            </div>
                            <div className="text-sm text-gray-500">
                              {validatorInfo.title}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                          {/* Score Badge */}
                          <div className={`px-4 py-2 rounded-lg font-bold text-lg ${
                            score.approved 
                              ? "bg-green-100 text-green-700" 
                              : "bg-amber-100 text-amber-700"
                          }`}>
                            {score.score.toFixed(1)}<span className="text-sm font-normal opacity-70">/10</span>
                          </div>
                          
                          {/* Approval Icon */}
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            score.approved ? "bg-green-500" : "bg-amber-500"
                          }`}>
                            <span className="text-white text-sm font-bold">
                              {score.approved ? "✓" : "!"}
                            </span>
                          </div>
                          
                          {/* Expand/Collapse Arrow */}
                          <div className={`transform transition-transform ${isExpanded ? "rotate-180" : ""}`}>
                            <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </div>
                        </div>
                      </button>

                      {/* Expanded Content - Validator's Detailed Feedback */}
                      {isExpanded && (
                        <div className="px-5 pb-5 pt-0 border-t border-gray-100">
                          <div className="pt-4 space-y-4">
                            
                            {/* Main Comment/Feedback */}
                            {(score.comment || score.feedback || score.reasoning || score.rationale) && (
                              <div className="bg-white rounded-lg p-4 border border-gray-200">
                                <div className="flex items-start gap-3">
                                  <div className="text-xl mt-0.5">💬</div>
                                  <div>
                                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                                      Validator's Assessment
                                    </div>
                                    <p className="text-gray-800 leading-relaxed">
                                      {score.comment || score.feedback || score.reasoning || score.rationale}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Strengths */}
                            {score.strengths && (
                              <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                                <div className="flex items-start gap-3">
                                  <div className="text-xl mt-0.5">💪</div>
                                  <div className="flex-1">
                                    <div className="text-xs font-semibold text-green-700 uppercase tracking-wider mb-2">
                                      Strengths
                                    </div>
                                    {Array.isArray(score.strengths) ? (
                                      <ul className="space-y-1">
                                        {score.strengths.map((s: string, i: number) => (
                                          <li key={i} className="text-green-800 text-sm flex items-start gap-2">
                                            <span className="text-green-500 mt-1">•</span>
                                            <span>{s}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    ) : (
                                      <p className="text-green-800 text-sm">{score.strengths}</p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Weaknesses / Areas for Improvement */}
                            {(score.weaknesses || score.improvements || score.suggestions) && (
                              <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
                                <div className="flex items-start gap-3">
                                  <div className="text-xl mt-0.5">🎯</div>
                                  <div className="flex-1">
                                    <div className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">
                                      Areas for Improvement
                                    </div>
                                    {Array.isArray(score.weaknesses || score.improvements || score.suggestions) ? (
                                      <ul className="space-y-1">
                                        {(score.weaknesses || score.improvements || score.suggestions).map((w: string, i: number) => (
                                          <li key={i} className="text-amber-800 text-sm flex items-start gap-2">
                                            <span className="text-amber-500 mt-1">•</span>
                                            <span>{w}</span>
                                          </li>
                                        ))}
                                      </ul>
                                    ) : (
                                      <p className="text-amber-800 text-sm">
                                        {score.weaknesses || score.improvements || score.suggestions}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Criteria Breakdown (if provided) */}
                            {score.criteria && Object.keys(score.criteria).length > 0 && (
                              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                                  📊 Criteria Breakdown
                                </div>
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                                  {Object.entries(score.criteria).map(([key, value]: [string, any]) => (
                                    <div key={key} className="text-center p-2 bg-white rounded-lg border border-gray-200">
                                      <div className="text-xs text-gray-500 capitalize mb-1">
                                        {key.replace(/_/g, ' ')}
                                      </div>
                                      <div className="text-lg font-semibold text-purple-600">
                                        {typeof value === 'number' ? value.toFixed(1) : value}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Fallback if no detailed feedback available */}
                            {!score.comment && !score.feedback && !score.reasoning && !score.rationale && 
                             !score.strengths && !score.weaknesses && !score.improvements && !score.suggestions && (
                              <div className="text-center py-4 text-gray-500 text-sm italic">
                                {score.approved 
                                  ? "This validator approved the content without additional comments."
                                  : "No detailed feedback provided by this validator."}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
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
              setSaveStatus("idle");
              setSavedPostId(null);
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
            View Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}