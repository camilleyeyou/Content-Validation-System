// portal/frontend/app/prompts/page.tsx
"use client";
import { useEffect, useState } from "react";

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
      setMsg(`Error loading agents: ${e.message}`);
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
      setMsg(`Error loading prompts: ${e.message}`);
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
      setMsg(`✅ Saved custom prompts for ${selectedAgent}`);
      await loadAgents();
      await loadPrompts(selectedAgent);
    } catch (e: any) {
      setMsg(`❌ Error: ${e.message}`);
    } finally {
      setSaving(false);
    }
  }

  async function resetToDefaults() {
    if (!selectedAgent) return;
    if (!confirm(`Reset ${selectedAgent} to default prompts?`)) return;

    setMsg("");
    try {
      await fetchJSON(`${API_BASE}/api/prompts/${selectedAgent}`, {
        method: "DELETE",
      });
      setMsg(`✅ Reset ${selectedAgent} to defaults`);
      await loadAgents();
      await loadPrompts(selectedAgent);
    } catch (e: any) {
      setMsg(`❌ Error: ${e.message}`);
    }
  }

  const hasChanges =
    prompts &&
    (systemPrompt !== prompts.system_prompt ||
      userPrompt !== prompts.user_prompt_template);

  return (
    <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold mb-2">Agent Prompts Manager</h1>
          <p className="text-sm text-zinc-600">
            Customize agent prompts to test different strategies without changing code
          </p>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          <strong>💡 Tip:</strong> Customize agent prompts to test different strategies. Changes
          take effect immediately on next batch run.
        </p>
      </div>

      {/* Agent Selector */}
      <div className="bg-white rounded-xl border border-zinc-200 p-6 shadow-sm">
        <label className="block text-sm font-semibold mb-3">Select Agent:</label>
        <div className="flex gap-3 flex-wrap">
          {agents.map((agent) => (
            <button
              key={agent.name}
              onClick={() => setSelectedAgent(agent.name)}
              className={`px-4 py-3 rounded-lg border-2 transition-all flex flex-col items-start gap-1 ${
                selectedAgent === agent.name
                  ? "border-blue-600 bg-blue-50"
                  : "border-zinc-200 bg-white hover:border-zinc-300"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="font-semibold text-sm">{agent.name}</span>
                {agent.has_custom_prompts && (
                  <span className="text-[10px] bg-blue-600 text-white px-2 py-0.5 rounded-full font-bold">
                    CUSTOM
                  </span>
                )}
              </div>
              <span className="text-xs text-zinc-600 text-left">{agent.description}</span>
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-zinc-200 p-12 text-center">
          <div className="inline-block w-8 h-8 border-4 border-zinc-200 border-t-blue-600 rounded-full animate-spin" />
          <p className="mt-4 text-sm text-zinc-600">Loading prompts...</p>
        </div>
      ) : prompts ? (
        <>
          {/* Controls */}
          <div className="bg-white rounded-xl border border-zinc-200 p-6 shadow-sm">
            <div className="flex gap-3 items-center flex-wrap">
              <button
                onClick={savePrompts}
                disabled={!hasChanges || saving}
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  hasChanges
                    ? "bg-blue-600 text-white hover:bg-blue-700"
                    : "bg-zinc-200 text-zinc-500 cursor-not-allowed"
                }`}
              >
                {saving ? "Saving..." : "Save Custom Prompts"}
              </button>

              <button
                onClick={resetToDefaults}
                disabled={!prompts.has_custom}
                className={`px-6 py-3 border rounded-lg font-semibold transition-all ${
                  prompts.has_custom
                    ? "border-zinc-300 hover:bg-zinc-50"
                    : "border-zinc-200 text-zinc-400 cursor-not-allowed"
                }`}
              >
                Reset to Defaults
              </button>

              <label className="flex items-center gap-2 ml-auto cursor-pointer">
                <input
                  type="checkbox"
                  checked={showDefaults}
                  onChange={(e) => setShowDefaults(e.target.checked)}
                  className="w-4 h-4 rounded border-zinc-300 text-blue-600 focus:ring-2 focus:ring-blue-500"
                />
                <span className="text-sm">Show default prompts</span>
              </label>

              {prompts.has_custom && (
                <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-semibold">
                  Using custom prompts
                </span>
              )}
            </div>

            {msg && (
              <div
                className={`mt-4 p-4 rounded-lg text-sm ${
                  msg.includes("❌")
                    ? "bg-red-50 text-red-800 border border-red-200"
                    : "bg-green-50 text-green-800 border border-green-200"
                }`}
              >
                {msg}
              </div>
            )}
          </div>

          {/* System Prompt */}
          <div className="bg-white rounded-xl border border-zinc-200 p-6 shadow-sm space-y-4">
            <div>
              <label className="block text-lg font-semibold mb-1">System Prompt</label>
              <p className="text-sm text-zinc-600">
                Defines the agent's persona, expertise, and evaluation criteria
              </p>
            </div>

            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              className={`w-full min-h-[300px] p-4 font-mono text-sm border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                prompts.has_custom ? "border-blue-600" : "border-zinc-300"
              }`}
            />

            {showDefaults && (
              <details className="text-sm">
                <summary className="cursor-pointer font-semibold text-zinc-700 hover:text-zinc-900 mb-2">
                  Default System Prompt
                </summary>
                <pre className="bg-zinc-50 p-4 rounded-lg overflow-auto whitespace-pre-wrap text-xs border border-zinc-200">
                  {prompts.default_system_prompt}
                </pre>
              </details>
            )}
          </div>

          {/* User Prompt Template */}
          <div className="bg-white rounded-xl border border-zinc-200 p-6 shadow-sm space-y-4">
            <div>
              <label className="block text-lg font-semibold mb-1">User Prompt Template</label>
              <p className="text-sm text-zinc-600">
                The prompt structure for validation/generation tasks
              </p>
            </div>

            <textarea
              value={userPrompt}
              onChange={(e) => setUserPrompt(e.target.value)}
              className={`w-full min-h-[300px] p-4 font-mono text-sm border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                prompts.has_custom ? "border-blue-600" : "border-zinc-300"
              }`}
            />

            {showDefaults && (
              <details className="text-sm">
                <summary className="cursor-pointer font-semibold text-zinc-700 hover:text-zinc-900 mb-2">
                  Default User Prompt Template
                </summary>
                <pre className="bg-zinc-50 p-4 rounded-lg overflow-auto whitespace-pre-wrap text-xs border border-zinc-200">
                  {prompts.default_user_prompt_template}
                </pre>
              </details>
            )}
          </div>
        </>
      ) : null}
    </main>
  );
}