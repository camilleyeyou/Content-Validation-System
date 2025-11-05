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
      <div className="p-8">
        <div className="text-center py-16">
          <div className="inline-block w-16 h-16 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mb-4" />
          <p className="text-gray-600">Loading inspiration sources...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose Your Inspiration</h2>
        <p className="text-gray-600">
          Select 1-3 sources that will fuel your content. Mix and match for unique angles!
        </p>
      </div>

      {/* Selection Counter */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-gray-700">Selected:</span>
          <span className={`text-lg font-bold ${
            state.inspirationSelections.length === 0 ? "text-gray-400" :
            state.inspirationSelections.length < 3 ? "text-blue-600" : "text-green-600"
          }`}>
            {state.inspirationSelections.length}/3
          </span>
        </div>
        {state.inspirationSelections.length > 0 && (
          <button
            onClick={() => setState(prev => ({ ...prev, inspirationSelections: [] }))}
            className="text-sm text-red-600 hover:text-red-700 font-medium"
          >
            Clear All
          </button>
        )}
      </div>

      {/* Selected Pills */}
      {state.inspirationSelections.length > 0 && (
        <div className="mb-6 p-4 bg-green-50 border-2 border-green-200 rounded-xl">
          <div className="flex flex-wrap gap-2">
            {state.inspirationSelections.map((sel, idx) => (
              <div key={idx} className="flex items-center gap-2 bg-white px-4 py-2 rounded-full border-2 border-green-400 shadow-sm">
                <span className="text-lg">
                  {sel.type === "news" && "📰"}
                  {sel.type === "memes" && "😄"}
                  {sel.type === "philosopher" && "🧠"}
                  {sel.type === "poet" && "✍️"}
                </span>
                <span className="text-sm font-semibold text-gray-900">
                  {sel.preview?.title || sel.preview?.name || sel.selected_id}
                </span>
                <button
                  onClick={() => toggleSelection(sel.type, sel.selected_id, sel.preview)}
                  className="ml-2 text-red-600 hover:text-red-700 font-bold"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-gray-200">
        {[
          { key: "news", label: "📰 News", count: sources?.news?.length || 0 },
          { key: "memes", label: "😄 Memes", count: sources?.memes?.length || 0 },
          { key: "philosophers", label: "🧠 Philosophy", count: sources?.philosophers?.length || 0 },
          { key: "poets", label: "✍️ Poetry", count: sources?.poets?.length || 0 },
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-6 py-3 font-semibold transition-all ${
              activeTab === tab.key
                ? "border-b-4 border-purple-600 text-purple-700"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="mb-8 max-h-[500px] overflow-y-auto pr-2">
        {activeTab === "news" && (
          <div className="space-y-3">
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
          <div className="grid md:grid-cols-2 gap-4">
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
          <div className="grid md:grid-cols-2 gap-4">
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
          <div className="grid md:grid-cols-2 gap-4">
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

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-200">
        <button
          onClick={onBack}
          className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50 transition-all"
        >
          ← Back
        </button>
        <button
          onClick={onNext}
          disabled={!canContinue}
          className={`px-8 py-3 rounded-xl font-bold transition-all flex items-center gap-2 ${
            canContinue
              ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl"
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          }`}
        >
          Continue to Style
          <span className="text-xl">→</span>
        </button>
      </div>
    </div>
  );
}

// Inspiration Card Component
function InspirationCard({ type, item, isSelected, onToggle }: any) {
  const [expanded, setExpanded] = useState(false);

  return (
    <button
      onClick={onToggle}
      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
        isSelected
          ? "border-green-500 bg-green-50 shadow-lg"
          : "border-gray-200 bg-white hover:border-purple-300 hover:shadow-md"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {type === "news" && (
            <>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-sm font-semibold text-blue-700 bg-blue-100 px-2 py-1 rounded">
                  {item.source}
                </span>
              </div>
              <h4 className="font-bold text-gray-900 mb-1 line-clamp-2">{item.title}</h4>
              <p className="text-sm text-gray-600 line-clamp-2">{item.description}</p>
            </>
          )}

          {type === "memes" && (
            <>
              <h4 className="font-bold text-gray-900 mb-2">{item.name}</h4>
              <p className="text-sm text-gray-600 mb-2">{item.context}</p>
              <p className="text-xs text-purple-700 bg-purple-50 px-2 py-1 rounded inline-block">
                {item.usage}
              </p>
            </>
          )}

          {type === "philosopher" && (
            <>
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-bold text-gray-900">{item.name}</h4>
                <span className="text-xs text-gray-500">({item.era})</span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{item.bio}</p>
              <div className="text-xs text-blue-600">
                {item.quote_count} workplace-relevant {item.quote_count === 1 ? "quote" : "quotes"}
              </div>
            </>
          )}

          {type === "poet" && (
            <>
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-bold text-gray-900">{item.name}</h4>
              </div>
              <p className="text-sm text-gray-600 mb-2">{item.bio}</p>
              <p className="text-xs text-purple-600">{item.style}</p>
            </>
          )}
        </div>

        {/* Selection Checkbox */}
        <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
          isSelected
            ? "bg-green-500 border-green-500"
            : "border-gray-300"
        }`}>
          {isSelected && <span className="text-white text-sm font-bold">✓</span>}
        </div>
      </div>
    </button>
  );
}