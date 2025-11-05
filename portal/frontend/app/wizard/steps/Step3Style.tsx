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
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Content Length & Style</h2>
        <p className="text-gray-600">
          Choose your target length and optional style modifiers to shape your post.
        </p>
      </div>

      {/* Length Selection */}
      <div className="mb-10">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Target Length</h3>
        <div className="grid md:grid-cols-4 gap-4">
          {lengths.map(length => (
            <button
              key={length.value}
              onClick={() => setState(prev => ({ ...prev, length: length.value }))}
              className={`relative p-5 rounded-xl border-2 transition-all text-left ${
                state.length === length.value
                  ? "border-purple-600 bg-purple-50 shadow-lg scale-105"
                  : "border-gray-200 bg-white hover:border-purple-300 hover:shadow-md"
              }`}
            >
              {length.recommended && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white text-xs font-bold px-3 py-1 rounded-full shadow-md">
                    RECOMMENDED
                  </span>
                </div>
              )}

              <div className="text-3xl mb-3">{length.icon}</div>
              <div className="font-bold text-gray-900 mb-1">{length.label}</div>
              <div className="text-sm text-purple-700 font-semibold mb-2">{length.words}</div>
              <div className="text-xs text-gray-600">{length.description}</div>

              {/* Selection Indicator */}
              {state.length === length.value && (
                <div className="absolute top-3 right-3 w-6 h-6 bg-purple-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">✓</span>
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Style Flags */}
      <div className="mb-8">
        <h3 className="text-lg font-bold text-gray-900 mb-2">Style Modifiers</h3>
        <p className="text-sm text-gray-600 mb-4">
          Optional: Select any that apply to add unique flavor to your content
        </p>
        <div className="grid md:grid-cols-3 gap-3">
          {styleOptions.map(option => {
            const isSelected = state.styleFlags.includes(option.value);
            return (
              <button
                key={option.value}
                onClick={() => toggleStyleFlag(option.value)}
                className={`p-4 rounded-xl border-2 transition-all text-left ${
                  isSelected
                    ? "border-blue-500 bg-blue-50 shadow-md"
                    : "border-gray-200 bg-white hover:border-blue-300"
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <span className="text-2xl">{option.icon}</span>
                  <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                    isSelected ? "bg-blue-500 border-blue-500" : "border-gray-300"
                  }`}>
                    {isSelected && <span className="text-white text-xs font-bold">✓</span>}
                  </div>
                </div>
                <div className="font-bold text-gray-900 text-sm mb-1">{option.label}</div>
                <div className="text-xs text-gray-600">{option.description}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Preview */}
      <div className="mb-8 p-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border-2 border-purple-200">
        <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span className="text-xl">👀</span>
          Your Content Profile
        </h4>
        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700">Length:</span>
            <span className="text-purple-700 font-bold">
              {lengths.find(l => l.value === state.length)?.label} 
              <span className="text-gray-600 font-normal ml-1">
                ({lengths.find(l => l.value === state.length)?.words})
              </span>
            </span>
          </div>
          {state.styleFlags.length > 0 && (
            <div className="flex items-start gap-2">
              <span className="font-semibold text-gray-700">Styles:</span>
              <div className="flex flex-wrap gap-2">
                {state.styleFlags.map(flag => {
                  const option = styleOptions.find(o => o.value === flag);
                  return (
                    <span key={flag} className="text-blue-700 bg-blue-100 px-2 py-1 rounded text-xs font-medium">
                      {option?.icon} {option?.label}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
          {state.styleFlags.length === 0 && (
            <div className="text-gray-500 italic text-xs">
              No style modifiers selected - post will use natural flow
            </div>
          )}
        </div>
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
          className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-bold hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
        >
          Continue to Persona
          <span className="text-xl">→</span>
        </button>
      </div>
    </div>
  );
}