// portal/frontend/app/wizard/steps/Step2Inspiration.tsx
"use client";
import { useEffect, useState } from "react";
import { WizardState } from "../page";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8001";

type Props = {
  state: WizardState;
  setState: React.Dispatch<React.SetStateAction<WizardState>>;
  onNext: () => void;
  onBack: () => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
};

export default function Step2Inspiration({ state, setState, onNext, onBack, loading, setLoading, setError }: Props) {
  const [activeTab, setActiveTab] = useState<"news" | "memes" | "philosophers" | "poets">("news");
  const [sources, setSources] = useState<any>(null);

  useEffect(() => {
    loadInspirationSources();
  }, []);

  async function loadInspirationSources() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/wizard/inspiration-sources`);
      const data = await response.json();
      
      if (!data.ok) {
        throw new Error("Failed to load inspiration sources");
      }
      
      setSources(data.sources);
      setState(prev => ({ ...prev, inspirationSources: data.sources }));
    } catch (e: any) {
      setError(e.message || "Failed to load inspiration sources");
    } finally {
      setLoading(false);
    }
  }

  const isSelected = (type: string, id: string) => {
    return state.inspirationSelections.some(s => s.type === type && s.selected_id === id);
  };

  const toggleSelection = (type: string, id: string, preview: any) => {
    const isCurrentlySelected = isSelected(type, id);
    
    if (isCurrentlySelected) {
      // Remove selection
      setState(prev => ({
        ...prev,
        inspirationSelections: prev.inspirationSelections.filter(
          s => !(s.type === type && s.selected_id === id)
        )
      }));
    } else {
      // Add selection (check limit)
      if (state.inspirationSelections.length >= 3) {
        setError("You can select up to 3 inspiration sources. Remove one to add another.");
        return;
      }
      
      setState(prev => ({
        ...prev,
        inspirationSelections: [...prev.inspirationSelections, { type, selected_id: id, preview }]
      }));
      setError("");
    }
  };

  const canContinue = state.inspirationSelections.length >= 1;

  if (loading && !sources) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-16 text-center">
            <div className="inline-block w-16 h-16 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mb-6" />
            <p className="text-gray-600 font-medium">Loading inspiration sources...</p>
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
            Choose Your Inspiration
          </h2>
          <p className="text-sm md:text-base text-gray-600 leading-relaxed">
            Select 1-3 sources that will fuel your content. Mix and match for unique angles.
          </p>
        </div>
      </div>

      {/* Selection Counter & Clear Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-6 md:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-600 uppercase tracking-wider">Selected:</span>
            <span className={`text-2xl font-semibold ${
              state.inspirationSelections.length === 0 ? "text-gray-400" :
              state.inspirationSelections.length < 3 ? "text-purple-600" : "text-green-600"
            }`}>
              {state.inspirationSelections.length}/3
            </span>
          </div>
          {state.inspirationSelections.length > 0 && (
            <button
              onClick={() => setState(prev => ({ ...prev, inspirationSelections: [] }))}
              className="text-sm text-red-600 hover:text-red-700 font-medium uppercase tracking-wider transition-colors duration-300"
            >
              Clear All
            </button>
          )}
        </div>
      </div>

      {/* Selected Pills Card */}
      {state.inspirationSelections.length > 0 && (
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 overflow-hidden">
          <div className="p-6 md:p-8">
            <h3 className="text-gray-900 text-lg font-semibold mb-4 flex items-center gap-2">
              <span className="text-xl">✦</span>
              Your Selections
            </h3>
            <div className="flex flex-wrap gap-3">
              {state.inspirationSelections.map((sel, idx) => (
                <div 
                  key={idx} 
                  className="flex items-center gap-3 bg-white px-5 py-2.5 rounded-lg border border-green-200 hover:border-green-300 transition-all duration-300 shadow-sm"
                >
                  <span className="text-lg">
                    {sel.type === "news" && "📰"}
                    {sel.type === "memes" && "😄"}
                    {sel.type === "philosopher" && "🧠"}
                    {sel.type === "poet" && "✍️"}
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {sel.preview?.title || sel.preview?.name || sel.selected_id}
                  </span>
                  <button
                    onClick={() => toggleSelection(sel.type, sel.selected_id, sel.preview)}
                    className="ml-2 text-red-500 hover:text-red-600 font-medium text-lg transition-colors duration-300"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tabs Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-6 md:p-8 border-b border-gray-200">
          <div className="flex flex-wrap gap-3">
            {[
              { key: "news", label: "News", icon: "📰", count: sources?.news?.length || 0 },
              { key: "memes", label: "Memes", icon: "😄", count: sources?.memes?.length || 0 },
              { key: "philosophers", label: "Philosophy", icon: "🧠", count: sources?.philosophers?.length || 0 },
              { key: "poets", label: "Poetry", icon: "✍️", count: sources?.poets?.length || 0 },
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as any)}
                className={`px-6 py-3 font-medium tracking-wider uppercase text-xs rounded-lg transition-all duration-300 ${
                  activeTab === tab.key
                    ? "text-white shadow-lg"
                    : "bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900 border border-gray-200"
                }`}
                style={activeTab === tab.key ? {
                  background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                } : {}}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="p-6 md:p-8 max-h-[600px] overflow-y-auto">
          {activeTab === "news" && (
            <div className="space-y-4">
              {sources?.news?.map((item: any) => (
                <InspirationCard
                  key={item.id}
                  type="news"
                  item={item}
                  isSelected={isSelected("news", item.id)}
                  onToggle={() => toggleSelection("news", item.id, item)}
                />
              ))}
            </div>
          )}

          {activeTab === "memes" && (
            <div className="grid sm:grid-cols-2 gap-4">
              {sources?.memes?.map((item: any) => (
                <InspirationCard
                  key={item.id}
                  type="memes"
                  item={item}
                  isSelected={isSelected("memes", item.id)}
                  onToggle={() => toggleSelection("memes", item.id, item)}
                />
              ))}
            </div>
          )}

          {activeTab === "philosophers" && (
            <div className="grid sm:grid-cols-2 gap-4">
              {sources?.philosophers?.map((item: any) => (
                <InspirationCard
                  key={item.id}
                  type="philosopher"
                  item={item}
                  isSelected={isSelected("philosopher", item.id)}
                  onToggle={() => toggleSelection("philosopher", item.id, item)}
                />
              ))}
            </div>
          )}

          {activeTab === "poets" && (
            <div className="grid sm:grid-cols-2 gap-4">
              {sources?.poets?.map((item: any) => (
                <InspirationCard
                  key={item.id}
                  type="poet"
                  item={item}
                  isSelected={isSelected("poet", item.id)}
                  onToggle={() => toggleSelection("poet", item.id, item)}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="px-8 py-4 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg font-medium tracking-wider uppercase text-sm border border-gray-200 hover:border-gray-300 transition-all duration-300"
        >
          ← Back
        </button>
        <button
          onClick={onNext}
          disabled={!canContinue}
          className={`px-12 py-4 rounded-lg font-medium tracking-wider uppercase text-sm transition-all duration-300 flex items-center justify-center gap-3 ${
            canContinue
              ? "text-white shadow-lg hover:shadow-xl"
              : "bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200"
          }`}
          style={canContinue ? {
            background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
          } : {}}
        >
          Continue to Style
          <span className="text-lg">→</span>
        </button>
      </div>
    </div>
  );
}

// Stripe-style Inspiration Card Component
function InspirationCard({ type, item, isSelected, onToggle }: any) {
  return (
    <button
      onClick={onToggle}
      className={`w-full text-left p-5 md:p-6 rounded-xl border transition-all duration-300 ${
        isSelected
          ? "border-green-300 bg-green-50 shadow-lg"
          : "border-gray-200 bg-white hover:border-purple-300 hover:shadow-md"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {type === "news" && (
            <>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-medium text-blue-700 bg-blue-100 px-3 py-1 rounded-md uppercase tracking-wider border border-blue-200">
                  {item.source}
                </span>
              </div>
              <h4 className="text-gray-900 mb-2 line-clamp-2 text-lg font-semibold leading-relaxed">
                {item.title}
              </h4>
              <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">
                {item.description}
              </p>
            </>
          )}

          {type === "memes" && (
            <>
              <h4 className="text-gray-900 mb-3 text-lg font-semibold">
                {item.name}
              </h4>
              <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                {item.context}
              </p>
              <p className="text-xs text-purple-700 bg-purple-100 px-3 py-1.5 rounded-md inline-block uppercase tracking-wider border border-purple-200 font-medium">
                {item.usage}
              </p>
            </>
          )}

          {type === "philosopher" && (
            <>
              <div className="flex items-center gap-3 mb-3">
                <h4 className="text-gray-900 text-lg font-semibold">{item.name}</h4>
                <span className="text-xs text-gray-500 font-medium">({item.era})</span>
              </div>
              <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                {item.bio}
              </p>
              <div className="text-xs text-purple-700 font-medium">
                {item.quote_count} workplace-relevant {item.quote_count === 1 ? "quote" : "quotes"}
              </div>
            </>
          )}

          {type === "poet" && (
            <>
              <div className="flex items-center gap-2 mb-3">
                <h4 className="text-gray-900 text-lg font-semibold">{item.name}</h4>
              </div>
              <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                {item.bio}
              </p>
              <p className="text-xs text-purple-700 font-medium italic">{item.style}</p>
            </>
          )}
        </div>

        {/* Selection Indicator */}
        <div className={`w-7 h-7 rounded-lg border flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
          isSelected
            ? "bg-green-500 border-green-500 shadow-lg"
            : "border-gray-300 bg-gray-50"
        }`}>
          {isSelected && <span className="text-white text-sm font-semibold">✓</span>}
        </div>
      </div>
    </button>
  );
}