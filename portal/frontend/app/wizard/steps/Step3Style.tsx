// portal/frontend/app/wizard/steps/Step3Style.tsx
"use client";
import { WizardState } from "../page";

type Props = {
  state: WizardState;
  setState: React.Dispatch<React.SetStateAction<WizardState>>;
  onNext: () => void;
  onBack: () => void;
};

export default function Step3Style({ state, setState, onNext, onBack }: Props) {
  const lengths = [
    { value: "very_short", label: "Very Short", words: "~50 words", description: "Ultra-punchy, headline style", icon: "⚡" },
    { value: "short", label: "Short", words: "~100 words", description: "Tweet-length, quick read", icon: "📱" },
    { value: "medium", label: "Medium", words: "~150 words", description: "LinkedIn sweet spot", icon: "📝", recommended: true },
    { value: "long", label: "Long", words: "~250 words", description: "Thought leadership piece", icon: "📚" },
  ];

  const styleOptions = [
    { value: "contrarian", label: "Contrarian", description: "Challenge conventional wisdom", icon: "🤔" },
    { value: "data_led", label: "Data-Led", description: "Lead with statistics", icon: "📊" },
    { value: "story_first", label: "Story First", description: "Open with anecdote", icon: "📖" },
    { value: "human_potential", label: "Human Potential", description: "Focus on growth", icon: "🌱" },
    { value: "outrageous_success", label: "Bold Success", description: "Celebrate big wins", icon: "🎯" },
    { value: "humble_brag", label: "Humble Brag", description: "Subtle success story", icon: "😌" },
  ];

  const toggleStyleFlag = (flag: string) => {
    setState(prev => ({
      ...prev,
      styleFlags: prev.styleFlags.includes(flag)
        ? prev.styleFlags.filter(f => f !== flag)
        : [...prev.styleFlags, flag]
    }));
  };

  return (
    <div className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
      <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
        {/* Header Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h2 className="text-3xl md:text-4xl font-serif font-light text-white mb-3 tracking-wide">
              Content Length & Style
            </h2>
            <p className="text-sm md:text-base text-gray-400 font-light leading-relaxed">
              Choose your target length and optional style modifiers to shape your post.
            </p>
          </div>
        </div>

        {/* Length Selection Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h3 className="text-2xl font-serif font-light text-white mb-6 tracking-wide">Target Length</h3>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
              {lengths.map(length => (
                <button
                  key={length.value}
                  onClick={() => setState(prev => ({ ...prev, length: length.value }))}
                  className={`relative p-6 md:p-7 rounded-sm border transition-all duration-300 text-left ${
                    state.length === length.value
                      ? "border-[#d4af37] bg-[#d4af37]/10 shadow-lg shadow-[#d4af37]/20"
                      : "border-white/10 bg-black/40 hover:border-[#d4af37]/30 hover:bg-black/60"
                  }`}
                >
                  {length.recommended && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <span className="bg-gradient-to-r from-[#d4af37] to-[#b8941f] text-black text-[10px] font-light px-3 py-1 rounded-sm shadow-lg uppercase tracking-widest">
                        Recommended
                      </span>
                    </div>
                  )}

                  <div className="text-3xl mb-4">{length.icon}</div>
                  <div className="font-serif text-white mb-2 text-lg font-light">{length.label}</div>
                  <div className="text-sm text-[#d4af37] font-light mb-3">{length.words}</div>
                  <div className="text-xs text-gray-400 font-light leading-relaxed">{length.description}</div>

                  {/* Selection Indicator */}
                  {state.length === length.value && (
                    <div className="absolute top-4 right-4 w-6 h-6 bg-[#d4af37] rounded-sm flex items-center justify-center shadow-lg">
                      <span className="text-black text-sm font-normal">✓</span>
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Style Flags Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h3 className="text-2xl font-serif font-light text-white mb-3 tracking-wide">Style Modifiers</h3>
            <p className="text-sm text-gray-400 mb-6 font-light leading-relaxed">
              Optional: Select any that apply to add unique flavor to your content
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {styleOptions.map(option => {
                const isSelected = state.styleFlags.includes(option.value);
                return (
                  <button
                    key={option.value}
                    onClick={() => toggleStyleFlag(option.value)}
                    className={`p-5 md:p-6 rounded-sm border transition-all duration-300 text-left ${
                      isSelected
                        ? "border-blue-500/50 bg-blue-500/10 shadow-lg shadow-blue-500/20"
                        : "border-white/10 bg-black/40 hover:border-blue-500/30 hover:bg-black/60"
                    }`}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <span className="text-2xl">{option.icon}</span>
                      <div className={`w-6 h-6 rounded-sm border flex items-center justify-center transition-all duration-300 ${
                        isSelected ? "bg-blue-500 border-blue-500 shadow-lg shadow-blue-500/30" : "border-white/20 bg-black/40"
                      }`}>
                        {isSelected && <span className="text-white text-xs font-normal">✓</span>}
                      </div>
                    </div>
                    <div className="font-serif text-white text-base mb-2 font-light">{option.label}</div>
                    <div className="text-xs text-gray-400 font-light leading-relaxed">{option.description}</div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Preview Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h4 className="font-serif text-white mb-5 flex items-center gap-3 text-xl font-light tracking-wide">
              <span className="text-2xl">✦</span>
              Your Content Profile
            </h4>
            <div className="space-y-4 text-sm">
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
                <span className="font-light text-gray-400 uppercase tracking-wider text-xs">Length:</span>
                <span className="text-[#d4af37] font-light text-base">
                  {lengths.find(l => l.value === state.length)?.label} 
                  <span className="text-gray-500 font-light ml-2">
                    ({lengths.find(l => l.value === state.length)?.words})
                  </span>
                </span>
              </div>
              {state.styleFlags.length > 0 && (
                <div className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-3">
                  <span className="font-light text-gray-400 uppercase tracking-wider text-xs">Styles:</span>
                  <div className="flex flex-wrap gap-2">
                    {state.styleFlags.map(flag => {
                      const option = styleOptions.find(o => o.value === flag);
                      return (
                        <span 
                          key={flag} 
                          className="text-blue-300 bg-blue-500/10 px-3 py-1.5 rounded-sm text-xs font-light uppercase tracking-wider border border-blue-500/30"
                        >
                          {option?.icon} {option?.label}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}
              {state.styleFlags.length === 0 && (
                <div className="text-gray-500 italic text-xs font-light pt-2 border-t border-white/10">
                  No style modifiers selected — post will use natural flow
                </div>
              )}
            </div>
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
            className="px-12 py-4 bg-gradient-to-br from-[#d4af37] to-[#b8941f] text-black rounded-sm font-light tracking-wider uppercase text-sm hover:shadow-2xl hover:shadow-[#d4af37]/20 transition-all duration-500 flex items-center justify-center gap-3"
          >
            Continue to Persona
            <span className="text-lg">→</span>
          </button>
        </div>
      </div>
    </div>
  );
}