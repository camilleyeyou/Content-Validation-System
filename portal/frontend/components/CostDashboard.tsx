// portal/frontend/components/CostDashboard.tsx
"use client";
import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8001";

type CostStats = {
  total_api_calls: number;
  total_posts: number;
  total_spent: number;
  avg_cost_per_post: number;
  avg_cost_per_call: number;
  openai_calls: number;
  gemini_calls: number;
  text_generation_calls: number;
  image_generation_calls: number;
  total_tokens: number;
  total_images: number;
};

type DailySummary = {
  date: string;
  total_cost: number;
  openai_cost: number;
  gemini_cost: number;
  text_generation_cost: number;
  image_generation_cost: number;
  posts_generated: number;
  images_generated: number;
  api_calls: number;
  total_tokens: number;
};

type PostCost = {
  batch_id: string;
  post_number: number;
  timestamp: string;
  total_cost: number;
  content_generation_cost: number;
  image_generation_cost: number;
  validation_cost: number;
  feedback_cost: number;
  total_tokens: number;
  api_calls: number;
};

type AgentCost = {
  agent_name: string;
  total_cost: number;
  api_calls: number;
  total_tokens: number;
  images_generated: number;
};

async function fetchJSON(url: string) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

export default function CostDashboard() {
  const [enabled, setEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<CostStats | null>(null);
  const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
  const [recentPosts, setRecentPosts] = useState<PostCost[]>([]);
  const [agentCosts, setAgentCosts] = useState<AgentCost[]>([]);
  const [daysFilter, setDaysFilter] = useState(7);

  async function loadCostData() {
    setLoading(true);
    try {
      // Check if enabled
      const statusRes = await fetchJSON(`${API_BASE}/api/costs/enabled`);
      setEnabled(statusRes.enabled);

      if (!statusRes.enabled) {
        setLoading(false);
        return;
      }

      // Load all cost data
      const [summaryRes, dailyRes, postsRes, agentsRes] = await Promise.all([
        fetchJSON(`${API_BASE}/api/costs/summary`),
        fetchJSON(`${API_BASE}/api/costs/daily`),
        fetchJSON(`${API_BASE}/api/costs/posts?limit=5`),
        fetchJSON(`${API_BASE}/api/costs/by-agent?days=${daysFilter}`),
      ]);

      setStats(summaryRes.stats);
      setDailySummary(dailyRes.summary);
      setRecentPosts(postsRes.posts || []);
      setAgentCosts(agentsRes.agents || []);
    } catch (error) {
      console.error("Failed to load cost data:", error);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCostData();
  }, [daysFilter]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center text-gray-500">Loading cost metrics...</div>
      </div>
    );
  }

  if (!enabled) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center">
          <div className="text-2xl mb-2">📊</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Cost Tracking Unavailable
          </h3>
          <p className="text-gray-600 text-sm">
            Cost tracking module not found. Please ensure cost_tracker.py is installed.
          </p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center text-gray-500">No cost data available</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Total Spent */}
      <div className="bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl shadow-lg p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold mb-2">
              ${stats.total_spent.toFixed(4)}
            </h2>
            <p className="text-purple-100 text-sm">Total API Spending (All Time)</p>
          </div>
          <div className="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center backdrop-blur-sm">
            <span className="text-4xl">💰</span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-white/20">
          <div>
            <div className="text-2xl font-bold">{stats.total_posts}</div>
            <div className="text-purple-100 text-xs">Posts Generated</div>
          </div>
          <div>
            <div className="text-2xl font-bold">{stats.total_api_calls}</div>
            <div className="text-purple-100 text-xs">Total API Calls</div>
          </div>
          <div>
            <div className="text-2xl font-bold">
              ${stats.avg_cost_per_post.toFixed(4)}
            </div>
            <div className="text-purple-100 text-xs">Avg Cost/Post</div>
          </div>
          <div>
            <div className="text-2xl font-bold">
              {(stats.total_tokens / 1000).toFixed(1)}K
            </div>
            <div className="text-purple-100 text-xs">Total Tokens</div>
          </div>
        </div>
      </div>

      {/* Provider Breakdown */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* OpenAI Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">AI</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">OpenAI</h3>
              <p className="text-xs text-gray-500">Text Generation</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <span className="text-sm text-gray-600">API Calls:</span>
              <span className="text-lg font-bold text-gray-900">
                {stats.openai_calls}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-sm text-gray-600">Text Generations:</span>
              <span className="text-lg font-bold text-gray-900">
                {stats.text_generation_calls}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-sm text-gray-600">Total Tokens:</span>
              <span className="text-lg font-bold text-gray-900">
                {(stats.total_tokens / 1000).toFixed(1)}K
              </span>
            </div>
          </div>
        </div>

        {/* Gemini Card */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">G</span>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Google Gemini</h3>
              <p className="text-xs text-gray-500">Image Generation</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <span className="text-sm text-gray-600">API Calls:</span>
              <span className="text-lg font-bold text-gray-900">
                {stats.gemini_calls}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-sm text-gray-600">Images Generated:</span>
              <span className="text-lg font-bold text-gray-900">
                {stats.total_images}
              </span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-sm text-gray-600">Avg Cost/Image:</span>
              <span className="text-lg font-bold text-gray-900">
                $0.039
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Today's Summary */}
      {dailySummary && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>📅</span>
            Today's Activity ({dailySummary.date})
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                ${dailySummary.total_cost.toFixed(4)}
              </div>
              <div className="text-xs text-gray-600 mt-1">Total Spent</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                {dailySummary.posts_generated}
              </div>
              <div className="text-xs text-gray-600 mt-1">Posts Created</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                {dailySummary.images_generated}
              </div>
              <div className="text-xs text-gray-600 mt-1">Images Generated</div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-2xl font-bold text-gray-900">
                {dailySummary.api_calls}
              </div>
              <div className="text-xs text-gray-600 mt-1">API Calls</div>
            </div>
          </div>
        </div>
      )}

      {/* Agent Costs */}
      {agentCosts.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <span>🤖</span>
              Cost by Agent
            </h3>
            <select
              value={daysFilter}
              onChange={(e) => setDaysFilter(Number(e.target.value))}
              className="text-sm border border-gray-300 rounded-md px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          </div>
          <div className="space-y-3">
            {agentCosts.map((agent) => {
              const percentage =
                stats.total_spent > 0
                  ? (agent.total_cost / stats.total_spent) * 100
                  : 0;
              return (
                <div key={agent.agent_name} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-700 font-medium">
                      {agent.agent_name}
                    </span>
                    <span className="text-gray-900 font-bold">
                      ${agent.total_cost.toFixed(4)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(percentage, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{agent.api_calls} calls</span>
                    <span>
                      {agent.images_generated > 0
                        ? `${agent.images_generated} images`
                        : `${(agent.total_tokens / 1000).toFixed(1)}K tokens`}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Post Costs */}
      {recentPosts.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <span>📝</span>
            Recent Post Costs
          </h3>
          <div className="space-y-3">
            {recentPosts.map((post) => (
              <div
                key={`${post.batch_id}-${post.post_number}`}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
              >
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <div className="font-medium text-gray-900">
                      Post #{post.post_number}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(post.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-gray-900">
                      ${post.total_cost.toFixed(4)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {post.api_calls} calls
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  {post.content_generation_cost > 0 && (
                    <div className="bg-green-50 rounded px-2 py-1 flex justify-between">
                      <span className="text-green-700">Content:</span>
                      <span className="text-green-900 font-medium">
                        ${post.content_generation_cost.toFixed(4)}
                      </span>
                    </div>
                  )}
                  {post.image_generation_cost > 0 && (
                    <div className="bg-blue-50 rounded px-2 py-1 flex justify-between">
                      <span className="text-blue-700">Image:</span>
                      <span className="text-blue-900 font-medium">
                        ${post.image_generation_cost.toFixed(4)}
                      </span>
                    </div>
                  )}
                  {post.validation_cost > 0 && (
                    <div className="bg-purple-50 rounded px-2 py-1 flex justify-between">
                      <span className="text-purple-700">Validation:</span>
                      <span className="text-purple-900 font-medium">
                        ${post.validation_cost.toFixed(4)}
                      </span>
                    </div>
                  )}
                  {post.feedback_cost > 0 && (
                    <div className="bg-amber-50 rounded px-2 py-1 flex justify-between">
                      <span className="text-amber-700">Feedback:</span>
                      <span className="text-amber-900 font-medium">
                        ${post.feedback_cost.toFixed(4)}
                      </span>
                    </div>
                  )}
                </div>

                <div className="mt-2 text-xs text-gray-500 text-right">
                  {(post.total_tokens / 1000).toFixed(1)}K tokens
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Refresh Button */}
      <div className="text-center">
        <button
          onClick={loadCostData}
          className="px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg font-medium hover:shadow-lg transition-all duration-200"
        >
          🔄 Refresh Cost Data
        </button>
      </div>
    </div>
  );
}