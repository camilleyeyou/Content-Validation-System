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
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <h2 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-3">
            Content Length & Style
          </h2>
          <p className="text-sm md:text-base text-gray-600 leading-relaxed">
            Choose your target length and optional style modifiers to shape your post.
          </p>
        </div>
      </div>

      {/* Length Selection Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <h3 className="text-2xl font-semibold text-gray-900 mb-6">Target Length</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5">
            {lengths.map(length => (
              <button
                key={length.value}
                onClick={() => setState(prev => ({ ...prev, length: length.value }))}
                className={`relative p-6 md:p-7 rounded-xl border transition-all duration-300 text-left ${
                  state.length === length.value
                    ? "border-purple-300 bg-purple-50 shadow-lg"
                    : "border-gray-200 bg-white hover:border-purple-200 hover:shadow-md"
                }`}
              >
                {length.recommended && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span 
                      className="text-white text-[10px] font-medium px-3 py-1 rounded-lg shadow-lg uppercase tracking-widest"
                      style={{
                        background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
                      }}
                    >
                      Recommended
                    </span>
                  </div>
                )}

                <div className="text-3xl mb-4">{length.icon}</div>
                <div className="text-gray-900 mb-2 text-lg font-semibold">{length.label}</div>
                <div className="text-sm text-purple-600 font-medium mb-3">{length.words}</div>
                <div className="text-xs text-gray-600 leading-relaxed">{length.description}</div>

                {/* Selection Indicator */}
                {state.length === length.value && (
                  <div className="absolute top-4 right-4 w-6 h-6 bg-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                    <span className="text-white text-sm font-semibold">✓</span>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Style Flags Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <h3 className="text-2xl font-semibold text-gray-900 mb-3">Style Modifiers</h3>
          <p className="text-sm text-gray-600 mb-6 leading-relaxed">
            Optional: Select any that apply to add unique flavor to your content
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {styleOptions.map(option => {
              const isSelected = state.styleFlags.includes(option.value);
              return (
                <button
                  key={option.value}
                  onClick={() => toggleStyleFlag(option.value)}
                  className={`p-5 md:p-6 rounded-xl border transition-all duration-300 text-left ${
                    isSelected
                      ? "border-blue-300 bg-blue-50 shadow-lg"
                      : "border-gray-200 bg-white hover:border-blue-200 hover:shadow-md"
                  }`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <span className="text-2xl">{option.icon}</span>
                    <div className={`w-6 h-6 rounded-lg border flex items-center justify-center transition-all duration-300 ${
                      isSelected ? "bg-blue-500 border-blue-500 shadow-lg" : "border-gray-300 bg-gray-50"
                    }`}>
                      {isSelected && <span className="text-white text-xs font-semibold">✓</span>}
                    </div>
                  </div>
                  <div className="text-gray-900 text-base mb-2 font-semibold">{option.label}</div>
                  <div className="text-xs text-gray-600 leading-relaxed">{option.description}</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Preview Card */}
      <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-8 md:p-10">
          <h4 className="text-gray-900 mb-5 flex items-center gap-3 text-xl font-semibold">
            <span className="text-2xl">✦</span>
            Your Content Profile
          </h4>
          <div className="space-y-4 text-sm">
            <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3">
              <span className="text-gray-600 uppercase tracking-wider text-xs font-medium">Length:</span>
              <span className="text-purple-700 font-semibold text-base">
                {lengths.find(l => l.value === state.length)?.label} 
                <span className="text-gray-500 font-normal ml-2">
                  ({lengths.find(l => l.value === state.length)?.words})
                </span>
              </span>
            </div>
            {state.styleFlags.length > 0 && (
              <div className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-3">
                <span className="text-gray-600 uppercase tracking-wider text-xs font-medium">Styles:</span>
                <div className="flex flex-wrap gap-2">
                  {state.styleFlags.map(flag => {
                    const option = styleOptions.find(o => o.value === flag);
                    return (
                      <span 
                        key={flag} 
                        className="text-blue-700 bg-blue-100 px-3 py-1.5 rounded-lg text-xs font-medium uppercase tracking-wider border border-blue-200"
                      >
                        {option?.icon} {option?.label}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
            {state.styleFlags.length === 0 && (
              <div className="text-gray-500 italic text-xs pt-2 border-t border-gray-200">
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
          className="px-8 py-4 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg font-medium tracking-wider uppercase text-sm border border-gray-200 hover:border-gray-300 transition-all duration-300"
        >
          ← Back
        </button>
        <button
          onClick={onNext}
          className="px-12 py-4 text-white rounded-lg font-medium tracking-wider uppercase text-sm shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center gap-3"
          style={{
            background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
          }}
        >
          Continue to Persona
          <span className="text-lg">→</span>
        </button>
      </div>
    </div>
  );
}