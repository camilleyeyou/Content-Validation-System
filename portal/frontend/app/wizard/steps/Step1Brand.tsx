// portal/frontend/app/wizard/steps/Step1Brand.tsx
"use client";
import { WizardState } from "../page";

type Props = {
  state: WizardState;
  setState: React.Dispatch<React.SetStateAction<WizardState>>;
  onNext: () => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  setError: (error: string) => void;
};

export default function Step1Brand({ state, setState, onNext }: Props) {
  const updateBrandSetting = (key: string, value: any) => {
    setState(prev => ({
      ...prev,
      brandSettings: {
        ...prev.brandSettings,
        [key]: value
      }
    }));
  };

  const handleContinue = () => {
    onNext();
  };

  const getSliderLabel = (type: string, value: number) => {
    if (type === "tone") {
      if (value < 30) return "Playful & Wacky";
      if (value < 70) return "Professional";
      return "Formal & Corporate";
    } else if (type === "pithiness") {
      if (value < 30) return "Punchy & Concise";
      if (value < 70) return "Balanced";
      return "Elaborate & Verbose";
    } else if (type === "jargon") {
      if (value < 30) return "Plain Language";
      if (value < 70) return "Moderate Business";
      return "Heavy VC-Speak";
    }
    return "";
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Brand Voice Settings</h2>
        <p className="text-gray-600">
          Customize how your brand speaks. Use the sliders to find your perfect voice.
        </p>
      </div>

      {/* Brand Pillars (Read-Only Context) */}
      <div className="mb-8 p-6 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border border-purple-200">
        <h3 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span className="text-xl">🎯</span>
          Jesse A. Eisenbalm Brand Essence
        </h3>
        <div className="grid md:grid-cols-3 gap-4 text-sm">
          <div>
            <div className="font-semibold text-purple-900 mb-1">Product</div>
            <div className="text-gray-700">Premium business lip balm</div>
          </div>
          <div>
            <div className="font-semibold text-purple-900 mb-1">Price</div>
            <div className="text-gray-700">$8.99</div>
          </div>
          <div>
            <div className="font-semibold text-purple-900 mb-1">Ritual</div>
            <div className="text-gray-700">Stop, Breathe, Balm</div>
          </div>
        </div>
        <div className="mt-4 text-xs text-gray-600 italic">
          💡 These core elements are automatically included in all generated content
        </div>
      </div>

      <div className="space-y-8">
        {/* Tone Slider */}
        <div>
          <label className="block mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-gray-900">Brand Tone</span>
              <span className="text-sm font-semibold text-purple-700 bg-purple-100 px-3 py-1 rounded-full">
                {getSliderLabel("tone", state.brandSettings.tone)}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500 font-medium min-w-[80px]">Wacky</span>
              <input
                type="range"
                min="0"
                max="100"
                value={state.brandSettings.tone}
                onChange={(e) => updateBrandSetting("tone", parseInt(e.target.value))}
                className="flex-1 h-3 bg-gradient-to-r from-yellow-300 via-blue-300 to-gray-400 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 
                  [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                  [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-purple-600
                  [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform"
              />
              <span className="text-xs text-gray-500 font-medium min-w-[80px] text-right">Formal</span>
            </div>
            <div className="mt-2 text-xs text-gray-600">
              {state.brandSettings.tone < 30 && "😄 Playful, meme-friendly, irreverent"}
              {state.brandSettings.tone >= 30 && state.brandSettings.tone < 70 && "💼 Conversational yet professional"}
              {state.brandSettings.tone >= 70 && "🎩 Executive-level formality"}
            </div>
          </label>
        </div>

        {/* Pithiness Slider */}
        <div>
          <label className="block mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-gray-900">Writing Style</span>
              <span className="text-sm font-semibold text-blue-700 bg-blue-100 px-3 py-1 rounded-full">
                {getSliderLabel("pithiness", state.brandSettings.pithiness)}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500 font-medium min-w-[80px]">Punchy</span>
              <input
                type="range"
                min="0"
                max="100"
                value={state.brandSettings.pithiness}
                onChange={(e) => updateBrandSetting("pithiness", parseInt(e.target.value))}
                className="flex-1 h-3 bg-gradient-to-r from-red-300 via-yellow-300 to-purple-400 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 
                  [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                  [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-blue-600
                  [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform"
              />
              <span className="text-xs text-gray-500 font-medium min-w-[80px] text-right">Baroque</span>
            </div>
            <div className="mt-2 text-xs text-gray-600">
              {state.brandSettings.pithiness < 30 && "⚡ Short, punchy sentences"}
              {state.brandSettings.pithiness >= 30 && state.brandSettings.pithiness < 70 && "📝 Balanced detail and brevity"}
              {state.brandSettings.pithiness >= 70 && "📚 Rich, elaborate storytelling"}
            </div>
          </label>
        </div>

        {/* Jargon Slider */}
        <div>
          <label className="block mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-gray-900">Language Level</span>
              <span className="text-sm font-semibold text-green-700 bg-green-100 px-3 py-1 rounded-full">
                {getSliderLabel("jargon", state.brandSettings.jargon)}
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500 font-medium min-w-[80px]">Plain</span>
              <input
                type="range"
                min="0"
                max="100"
                value={state.brandSettings.jargon}
                onChange={(e) => updateBrandSetting("jargon", parseInt(e.target.value))}
                className="flex-1 h-3 bg-gradient-to-r from-green-300 via-blue-300 to-indigo-400 rounded-full appearance-none cursor-pointer
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 
                  [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                  [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-green-600
                  [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform"
              />
              <span className="text-xs text-gray-500 font-medium min-w-[80px] text-right">VC-Speak</span>
            </div>
            <div className="mt-2 text-xs text-gray-600">
              {state.brandSettings.jargon < 30 && "🗣️ Simple, accessible language"}
              {state.brandSettings.jargon >= 30 && state.brandSettings.jargon < 70 && "💼 Moderate business terminology"}
              {state.brandSettings.jargon >= 70 && "🚀 Heavy startup/VC buzzwords"}
            </div>
          </label>
        </div>

        {/* Custom Brand Additions */}
        <div>
          <label className="block">
            <div className="mb-2">
              <span className="font-bold text-gray-900">Custom Brand Additions</span>
              <span className="text-xs text-gray-500 ml-2">(Optional)</span>
            </div>
            <textarea
              value={state.brandSettings.custom}
              onChange={(e) => updateBrandSetting("custom", e.target.value)}
              placeholder="Add any specific brand guidelines, themes, or messaging you want to emphasize..."
              className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all min-h-[120px] text-sm"
              maxLength={500}
            />
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="text-gray-500">
                💡 Example: "Always emphasize mindfulness" or "Use humor when appropriate"
              </span>
              <span className="text-gray-400">
                {state.brandSettings.custom.length}/500
              </span>
            </div>
          </label>
        </div>
      </div>

      {/* Preview Box */}
      <div className="mt-8 p-6 bg-gray-50 border-2 border-dashed border-gray-300 rounded-xl">
        <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span className="text-lg">👀</span>
          Voice Preview
        </h4>
        <div className="text-sm text-gray-700 space-y-2">
          <p>
            <strong>Tone:</strong> {getSliderLabel("tone", state.brandSettings.tone)} • 
            <strong className="ml-2">Style:</strong> {getSliderLabel("pithiness", state.brandSettings.pithiness)} • 
            <strong className="ml-2">Language:</strong> {getSliderLabel("jargon", state.brandSettings.jargon)}
          </p>
          {state.brandSettings.custom && (
            <p>
              <strong>Custom:</strong> {state.brandSettings.custom}
            </p>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={handleContinue}
          className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-bold hover:from-purple-700 hover:to-blue-700 transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
        >
          Continue to Inspiration
          <span className="text-xl">→</span>
        </button>
      </div>
    </div>
  );
}