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
      <div className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
        <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
            <div className="p-16 text-center">
              <div className="inline-block w-16 h-16 border-4 border-[#d4af37]/20 border-t-[#d4af37] rounded-full animate-spin mb-6" />
              <p className="text-gray-400 font-light tracking-wide">Loading inspiration sources...</p>
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
              Choose Your Inspiration
            </h2>
            <p className="text-sm md:text-base text-gray-400 font-light leading-relaxed">
              Select 1-3 sources that will fuel your content. Mix and match for unique angles.
            </p>
          </div>
        </div>

        {/* Selection Counter & Clear Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-6 md:p-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="text-sm font-light text-gray-400 uppercase tracking-wider">Selected:</span>
              <span className={`text-2xl font-serif font-light ${
                state.inspirationSelections.length === 0 ? "text-gray-600" :
                state.inspirationSelections.length < 3 ? "text-[#d4af37]" : "text-emerald-400"
              }`}>
                {state.inspirationSelections.length}/3
              </span>
            </div>
            {state.inspirationSelections.length > 0 && (
              <button
                onClick={() => setState(prev => ({ ...prev, inspirationSelections: [] }))}
                className="text-sm text-red-400 hover:text-red-300 font-light uppercase tracking-wider transition-colors duration-300"
              >
                Clear All
              </button>
            )}
          </div>
        </div>

        {/* Selected Pills Card */}
        {state.inspirationSelections.length > 0 && (
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-emerald-500/30 shadow-2xl overflow-hidden mb-8">
            <div className="p-6 md:p-8">
              <h3 className="font-serif text-white text-lg font-light tracking-wide mb-4 flex items-center gap-2">
                <span className="text-xl">✦</span>
                Your Selections
              </h3>
              <div className="flex flex-wrap gap-3">
                {state.inspirationSelections.map((sel, idx) => (
                  <div 
                    key={idx} 
                    className="flex items-center gap-3 bg-emerald-500/10 px-5 py-2.5 rounded-sm border border-emerald-500/30 hover:border-emerald-500/50 transition-all duration-300"
                  >
                    <span className="text-lg">
                      {sel.type === "news" && "📰"}
                      {sel.type === "memes" && "😄"}
                      {sel.type === "philosopher" && "🧠"}
                      {sel.type === "poet" && "✍️"}
                    </span>
                    <span className="text-sm font-light text-white">
                      {sel.preview?.title || sel.preview?.name || sel.selected_id}
                    </span>
                    <button
                      onClick={() => toggleSelection(sel.type, sel.selected_id, sel.preview)}
                      className="ml-2 text-red-400 hover:text-red-300 font-light text-lg transition-colors duration-300"
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
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-6 md:p-8 border-b border-white/10">
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
                  className={`px-6 py-3 font-light tracking-wider uppercase text-xs rounded-sm transition-all duration-300 ${
                    activeTab === tab.key
                      ? "bg-[#d4af37] text-black"
                      : "bg-white/5 text-gray-400 hover:bg-white/10 hover:text-gray-300 border border-white/10"
                  }`}
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
            className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white rounded-sm font-light tracking-wider uppercase text-sm border border-white/10 hover:border-white/20 transition-all duration-300"
          >
            ← Back
          </button>
          <button
            onClick={onNext}
            disabled={!canContinue}
            className={`px-12 py-4 rounded-sm font-light tracking-wider uppercase text-sm transition-all duration-500 flex items-center justify-center gap-3 ${
              canContinue
                ? "bg-gradient-to-br from-[#d4af37] to-[#b8941f] text-black hover:shadow-2xl hover:shadow-[#d4af37]/20"
                : "bg-white/5 text-gray-600 cursor-not-allowed border border-white/10"
            }`}
          >
            Continue to Style
            <span className="text-lg">→</span>
          </button>
        </div>
      </div>
    </div>
  );
}

// Luxury Inspiration Card Component
function InspirationCard({ type, item, isSelected, onToggle }: any) {
  return (
    <button
      onClick={onToggle}
      className={`w-full text-left p-5 md:p-6 rounded-sm border transition-all duration-300 ${
        isSelected
          ? "border-emerald-500/50 bg-emerald-500/10 shadow-lg shadow-emerald-500/20"
          : "border-white/10 bg-black/40 hover:border-[#d4af37]/30 hover:bg-black/60"
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {type === "news" && (
            <>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-light text-blue-300 bg-blue-500/10 px-3 py-1 rounded-sm uppercase tracking-wider border border-blue-500/30">
                  {item.source}
                </span>
              </div>
              <h4 className="font-serif text-white mb-2 line-clamp-2 text-lg font-light leading-relaxed">
                {item.title}
              </h4>
              <p className="text-sm text-gray-400 line-clamp-2 font-light leading-relaxed">
                {item.description}
              </p>
            </>
          )}

          {type === "memes" && (
            <>
              <h4 className="font-serif text-white mb-3 text-lg font-light">
                {item.name}
              </h4>
              <p className="text-sm text-gray-400 mb-3 font-light leading-relaxed">
                {item.context}
              </p>
              <p className="text-xs text-purple-300 bg-purple-500/10 px-3 py-1.5 rounded-sm inline-block uppercase tracking-wider border border-purple-500/30 font-light">
                {item.usage}
              </p>
            </>
          )}

          {type === "philosopher" && (
            <>
              <div className="flex items-center gap-3 mb-3">
                <h4 className="font-serif text-white text-lg font-light">{item.name}</h4>
                <span className="text-xs text-gray-500 font-light">({item.era})</span>
              </div>
              <p className="text-sm text-gray-400 mb-3 font-light leading-relaxed">
                {item.bio}
              </p>
              <div className="text-xs text-[#d4af37] font-light">
                {item.quote_count} workplace-relevant {item.quote_count === 1 ? "quote" : "quotes"}
              </div>
            </>
          )}

          {type === "poet" && (
            <>
              <div className="flex items-center gap-2 mb-3">
                <h4 className="font-serif text-white text-lg font-light">{item.name}</h4>
              </div>
              <p className="text-sm text-gray-400 mb-3 font-light leading-relaxed">
                {item.bio}
              </p>
              <p className="text-xs text-purple-300 font-light italic">{item.style}</p>
            </>
          )}
        </div>

        {/* Luxury Selection Indicator */}
        <div className={`w-7 h-7 rounded-sm border flex items-center justify-center flex-shrink-0 transition-all duration-300 ${
          isSelected
            ? "bg-emerald-500 border-emerald-500 shadow-lg shadow-emerald-500/30"
            : "border-white/20 bg-black/40"
        }`}>
          {isSelected && <span className="text-black text-sm font-normal">✓</span>}
        </div>
      </div>
    </button>
  );
}