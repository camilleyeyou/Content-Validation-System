// portal/frontend/app/prompts/page.tsx
"use client";
import { useEffect, useState } from "react";
import Link from "next/link";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8001";

type Agent = {
  name: string;
  description: string;
  has_custom_prompts: boolean;
};

type AgentPrompts = {
  agent_name: string;
  has_custom: boolean;
  system_prompt: string;
  user_prompt_template: string;
  default_system_prompt: string;
  default_user_prompt_template: string;
};

export default function PromptsManager() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("");
  const [prompts, setPrompts] = useState<AgentPrompts | null>(null);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [userPrompt, setUserPrompt] = useState("");
  const [showDefaults, setShowDefaults] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [msg, setMsg] = useState("");
  const [saving, setSaving] = useState(false);
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

  async function loadAgents() {
    try {
      const data = await fetchJSON(`${API_BASE}/api/prompts/agents`);
      setAgents(data);
      if (data.length > 0 && !selectedAgent) {
        setSelectedAgent(data[0].name);
      }
    } catch (e: any) {
      setMsg(`❌ Error loading agents: ${e.message}`);
    }
  }

  async function loadPrompts(agentName: string) {
    setLoading(true);
    try {
      const data = await fetchJSON(`${API_BASE}/api/prompts/${agentName}`);
      setPrompts(data);
      setSystemPrompt(data.system_prompt);
      setUserPrompt(data.user_prompt_template);
    } catch (e: any) {
      setMsg(`❌ Error loading prompts: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      loadPrompts(selectedAgent);
    }
  }, [selectedAgent]);

  async function savePrompts() {
    if (!selectedAgent) return;
    setSaving(true);
    setMsg("");
    try {
      await fetchJSON(`${API_BASE}/api/prompts/${selectedAgent}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          system_prompt: systemPrompt,
          user_prompt_template: userPrompt,
        }),
      });
      setMsg(`✅ Successfully saved custom prompts for ${selectedAgent}`);
      await loadAgents();
      await loadPrompts(selectedAgent);
    } catch (e: any) {
      setMsg(`❌ Save Error: ${e.message}`);
    } finally {
      setSaving(false);
    }
  }

  async function resetToDefaults() {
    if (!selectedAgent) return;
    if (!confirm(`⚠️ Reset ${selectedAgent} to default prompts?\n\nThis will permanently delete your custom prompts.`))
      return;

    setMsg("");
    try {
      await fetchJSON(`${API_BASE}/api/prompts/${selectedAgent}`, {
        method: "DELETE",
      });
      setMsg(`✅ Successfully reset ${selectedAgent} to defaults`);
      await loadAgents();
      await loadPrompts(selectedAgent);
    } catch (e: any) {
      setMsg(`❌ Reset Error: ${e.message}`);
    }
  }

  const hasChanges =
    prompts &&
    (systemPrompt !== prompts.system_prompt || userPrompt !== prompts.user_prompt_template);

  return (
    <main className="min-h-screen bg-gradient-to-br from-zinc-50 via-purple-50/20 to-zinc-50">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Enhanced Header */}
        <div className="bg-white rounded-2xl border border-zinc-200 p-8 shadow-sm">
          <div className="flex items-start justify-between gap-6 mb-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-600 to-purple-700 rounded-xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                  🤖
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-zinc-900">AI Agent Prompts Manager</h1>
                  <p className="text-sm text-zinc-600 mt-1">
                    Fine-tune agent behavior and customize content generation strategies
                  </p>
                </div>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setShowGuide(!showGuide)}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-all flex items-center gap-2"
              >
                <span className="text-lg">📖</span>
                {showGuide ? "Hide" : "Show"} Guide
              </button>
              <Link
                href="/"
                className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-all flex items-center gap-2"
              >
                <span className="text-lg">←</span>
                Dashboard
              </Link>
            </div>
          </div>

          {/* Prompt Engineering Guide */}
          {showGuide && (
            <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl p-6 border border-purple-200 mt-4">
              <h3 className="text-lg font-bold text-zinc-900 mb-4 flex items-center gap-2">
                <span className="text-2xl">💡</span>
                Understanding AI Agent Prompts
              </h3>
              <div className="grid md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <h4 className="font-bold text-zinc-900 mb-2 flex items-center gap-2">
                      <span className="text-lg">🎯</span>
                      System Prompt
                    </h4>
                    <p className="text-sm text-zinc-700 mb-3">
                      Defines the agent's core identity, expertise, role, and behavioral guidelines. This is like
                      giving the AI its "personality" and "job description."
                    </p>
                    <div className="bg-purple-50 rounded p-3 text-xs text-purple-900 border border-purple-200">
                      <strong>Key Elements:</strong>
                      <ul className="mt-2 space-y-1 ml-4 list-disc">
                        <li>Agent's role and expertise area</li>
                        <li>Tone and communication style</li>
                        <li>Quality criteria and standards</li>
                        <li>Output format guidelines</li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <h4 className="font-bold text-zinc-900 mb-2 flex items-center gap-2">
                      <span className="text-lg">📝</span>
                      User Prompt Template
                    </h4>
                    <p className="text-sm text-zinc-700 mb-3">
                      The structured template used for each specific task. Contains placeholders for dynamic content
                      that gets filled in during generation.
                    </p>
                    <div className="bg-blue-50 rounded p-3 text-xs text-blue-900 border border-blue-200">
                      <strong>Common Placeholders:</strong>
                      <ul className="mt-2 space-y-1 ml-4 list-disc">
                        <li>
                          <code className="bg-blue-100 px-1 rounded">{"{{target_type}}"}</code> - MEMBER or ORG
                        </li>
                        <li>
                          <code className="bg-blue-100 px-1 rounded">{"{{lifecycle}}"}</code> - User lifecycle stage
                        </li>
                        <li>
                          <code className="bg-blue-100 px-1 rounded">{"{{content}}"}</code> - Generated content to
                          validate
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4 border border-zinc-200">
                    <h4 className="font-bold text-zinc-900 mb-2 flex items-center gap-2">
                      <span className="text-lg">🔄</span>
                      How It Works
                    </h4>
                    <div className="space-y-3 text-sm text-zinc-700">
                      <div className="flex gap-3">
                        <div className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0">
                          1
                        </div>
                        <p>
                          <strong>Custom prompts override defaults</strong> - If you set custom prompts, they
                          completely replace the default behavior
                        </p>
                      </div>
                      <div className="flex gap-3">
                        <div className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0">
                          2
                        </div>
                        <p>
                          <strong>Placeholders get replaced at runtime</strong> - Dynamic values are injected when
                          the agent processes each task
                        </p>
                      </div>
                      <div className="flex gap-3">
                        <div className="w-6 h-6 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold text-xs flex-shrink-0">
                          3
                        </div>
                        <p>
                          <strong>Changes take effect immediately</strong> - Next batch run will use your updated
                          prompts
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-lg p-4 border border-amber-200">
                    <h4 className="font-bold text-amber-900 mb-2 flex items-center gap-2">
                      <span className="text-lg">⚠️</span>
                      Best Practices
                    </h4>
                    <ul className="space-y-2 text-xs text-amber-900">
                      <li className="flex gap-2">
                        <span>•</span>
                        <span>Test changes incrementally - modify one agent at a time</span>
                      </li>
                      <li className="flex gap-2">
                        <span>•</span>
                        <span>Keep defaults visible to understand baseline behavior</span>
                      </li>
                      <li className="flex gap-2">
                        <span>•</span>
                        <span>Be specific about desired outputs and constraints</span>
                      </li>
                      <li className="flex gap-2">
                        <span>•</span>
                        <span>Document your changes for team collaboration</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Agent Selector with Enhanced UI */}
        <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
          <div className="mb-5">
            <h2 className="text-xl font-bold text-zinc-900 mb-1">Select Agent to Configure</h2>
            <p className="text-sm text-zinc-600">
              Choose an agent to view and customize its prompts
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <button
                key={agent.name}
                onClick={() => setSelectedAgent(agent.name)}
                className={`relative px-5 py-4 rounded-xl border-2 transition-all text-left ${
                  selectedAgent === agent.name
                    ? "border-purple-600 bg-gradient-to-br from-purple-50 to-purple-100 shadow-lg"
                    : "border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-md"
                }`}
              >
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-bold text-base text-zinc-900">{agent.name}</span>
                      {agent.has_custom_prompts && (
                        <span className="text-[10px] bg-purple-600 text-white px-2 py-0.5 rounded-full font-bold">
                          CUSTOM
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-zinc-600 leading-relaxed">{agent.description}</p>
                  </div>
                  {selectedAgent === agent.name && (
                    <div className="w-5 h-5 bg-purple-600 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-xs">✓</span>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="bg-white rounded-2xl border border-zinc-200 p-16 text-center shadow-sm">
            <div className="inline-block w-12 h-12 border-4 border-zinc-200 border-t-purple-600 rounded-full animate-spin" />
            <p className="mt-6 text-lg font-semibold text-zinc-900">Loading agent prompts...</p>
            <p className="mt-2 text-sm text-zinc-600">Please wait while we fetch the configuration</p>
          </div>
        ) : prompts ? (
          <>
            {/* Control Panel */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="flex gap-3 items-center flex-wrap mb-5">
                <button
                  onClick={savePrompts}
                  disabled={!hasChanges || saving}
                  className={`px-8 py-3 rounded-xl font-bold transition-all shadow-lg ${
                    hasChanges
                      ? "bg-gradient-to-r from-purple-600 to-purple-700 text-white hover:from-purple-700 hover:to-purple-800 shadow-purple-500/30"
                      : "bg-zinc-200 text-zinc-500 cursor-not-allowed"
                  }`}
                >
                  {saving ? (
                    <span className="flex items-center gap-2">
                      <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Saving...
                    </span>
                  ) : (
                    "💾 Save Custom Prompts"
                  )}
                </button>

                <button
                  onClick={resetToDefaults}
                  disabled={!prompts.has_custom}
                  className={`px-8 py-3 border-2 rounded-xl font-bold transition-all ${
                    prompts.has_custom
                      ? "border-zinc-300 bg-white text-zinc-900 hover:bg-zinc-50 hover:border-zinc-400"
                      : "border-zinc-200 text-zinc-400 cursor-not-allowed bg-zinc-50"
                  }`}
                >
                  🔄 Reset to Defaults
                </button>

                <label className="flex items-center gap-2 ml-auto cursor-pointer px-4 py-3 bg-zinc-50 rounded-xl border border-zinc-200 hover:bg-zinc-100 transition-all">
                  <input
                    type="checkbox"
                    checked={showDefaults}
                    onChange={(e) => setShowDefaults(e.target.checked)}
                    className="w-4 h-4 rounded border-zinc-300 text-purple-600 focus:ring-2 focus:ring-purple-500"
                  />
                  <span className="text-sm font-medium text-zinc-900">Show default prompts</span>
                </label>

                {prompts.has_custom && (
                  <div className="px-4 py-2 bg-purple-100 text-purple-900 rounded-xl text-sm font-bold border border-purple-200">
                    ✨ Using custom prompts
                  </div>
                )}
              </div>

              {hasChanges && (
                <div className="mb-5 p-4 bg-amber-50 border-2 border-amber-200 rounded-xl">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">⚠️</span>
                    <div>
                      <p className="text-sm font-bold text-amber-900 mb-1">Unsaved Changes Detected</p>
                      <p className="text-xs text-amber-800">
                        You have modified the prompts. Click "Save Custom Prompts" to apply these changes to future
                        batch runs.
                      </p>
                    </div>
                  </div>
                </div>
              )}

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

            {/* System Prompt Editor */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="mb-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-purple-600 text-white rounded-lg flex items-center justify-center font-bold text-sm">
                    S
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-zinc-900">System Prompt</h2>
                    <p className="text-sm text-zinc-600">
                      Defines the agent's identity, expertise, and behavioral guidelines
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative">
                <textarea
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  placeholder="Enter the system prompt that defines the agent's core behavior..."
                  className={`w-full min-h-[350px] p-5 font-mono text-sm border-2 rounded-xl focus:outline-none focus:ring-4 transition-all resize-y ${
                    prompts.has_custom
                      ? "border-purple-600 focus:ring-purple-500/20 bg-purple-50/30"
                      : "border-zinc-300 focus:ring-purple-500/20"
                  }`}
                />
                <div className="absolute top-3 right-3 text-xs text-zinc-400 font-mono bg-white px-2 py-1 rounded border border-zinc-200">
                  {systemPrompt.length} chars
                </div>
              </div>

              {showDefaults && (
                <details className="mt-5">
                  <summary className="cursor-pointer font-bold text-zinc-900 hover:text-purple-600 transition-colors px-4 py-3 bg-zinc-50 rounded-xl border border-zinc-200 hover:border-purple-300">
                    📄 View Default System Prompt
                  </summary>
                  <div className="mt-3 bg-zinc-900 p-5 rounded-xl border border-zinc-700">
                    <pre className="text-xs text-zinc-100 overflow-auto whitespace-pre-wrap leading-relaxed font-mono">
                      {prompts.default_system_prompt}
                    </pre>
                  </div>
                </details>
              )}
            </div>

            {/* User Prompt Template Editor */}
            <div className="bg-white rounded-2xl border border-zinc-200 p-6 shadow-sm">
              <div className="mb-5">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-sm">
                    U
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-zinc-900">User Prompt Template</h2>
                    <p className="text-sm text-zinc-600">
                      The structured template for task-specific instructions with dynamic placeholders
                    </p>
                  </div>
                </div>
              </div>

              <div className="mb-4 p-4 bg-blue-50 rounded-xl border border-blue-200">
                <p className="text-sm text-blue-900 font-medium mb-2">
                  💡 Available Placeholders (automatically replaced at runtime):
                </p>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                  <code className="bg-blue-100 text-blue-900 px-2 py-1 rounded font-mono">
                    {"{{target_type}}"}
                  </code>
                  <code className="bg-blue-100 text-blue-900 px-2 py-1 rounded font-mono">
                    {"{{lifecycle}}"}
                  </code>
                  <code className="bg-blue-100 text-blue-900 px-2 py-1 rounded font-mono">{"{{content}}"}</code>
                  <code className="bg-blue-100 text-blue-900 px-2 py-1 rounded font-mono">
                    {"{{commentary}}"}
                  </code>
                  <code className="bg-blue-100 text-blue-900 px-2 py-1 rounded font-mono">
                    {"{{description}}"}
                  </code>
                </div>
              </div>

              <div className="relative">
                <textarea
                  value={userPrompt}
                  onChange={(e) => setUserPrompt(e.target.value)}
                  placeholder="Enter the user prompt template with placeholders..."
                  className={`w-full min-h-[350px] p-5 font-mono text-sm border-2 rounded-xl focus:outline-none focus:ring-4 transition-all resize-y ${
                    prompts.has_custom
                      ? "border-purple-600 focus:ring-purple-500/20 bg-purple-50/30"
                      : "border-zinc-300 focus:ring-purple-500/20"
                  }`}
                />
                <div className="absolute top-3 right-3 text-xs text-zinc-400 font-mono bg-white px-2 py-1 rounded border border-zinc-200">
                  {userPrompt.length} chars
                </div>
              </div>

              {showDefaults && (
                <details className="mt-5">
                  <summary className="cursor-pointer font-bold text-zinc-900 hover:text-purple-600 transition-colors px-4 py-3 bg-zinc-50 rounded-xl border border-zinc-200 hover:border-purple-300">
                    📄 View Default User Prompt Template
                  </summary>
                  <div className="mt-3 bg-zinc-900 p-5 rounded-xl border border-zinc-700">
                    <pre className="text-xs text-zinc-100 overflow-auto whitespace-pre-wrap leading-relaxed font-mono">
                      {prompts.default_user_prompt_template}
                    </pre>
                  </div>
                </details>
              )}
            </div>
          </>
        ) : null}
      </div>
    </main>
  );
}