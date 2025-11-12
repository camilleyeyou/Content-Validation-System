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
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <h2 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-3">
            Brand Voice Settings
          </h2>
          <p className="text-sm md:text-base text-gray-600 leading-relaxed">
            Customize how your brand speaks. Use the sliders to find your perfect voice.
          </p>
        </div>
      </div>

      {/* Brand Pillars Card */}
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl border border-purple-100 overflow-hidden">
        <div className="p-8 md:p-10">
          <h3 className="text-gray-900 mb-6 flex items-center gap-3 text-xl md:text-2xl font-semibold">
            <span className="text-2xl">✦</span>
            Jesse A. Eisenbalm Brand Essence
          </h3>
          <div className="grid sm:grid-cols-3 gap-6 md:gap-8 text-sm">
            <div>
              <div className="font-semibold text-purple-700 mb-2 uppercase tracking-wider text-xs">Product</div>
              <div className="text-gray-700">Premium business lip balm</div>
            </div>
            <div>
              <div className="font-semibold text-purple-700 mb-2 uppercase tracking-wider text-xs">Price</div>
              <div className="text-gray-700">$8.99</div>
            </div>
            <div>
              <div className="font-semibold text-purple-700 mb-2 uppercase tracking-wider text-xs">Ritual</div>
              <div className="text-gray-700">Stop, Breathe, Apply</div>
            </div>
          </div>
          <div className="mt-6 text-xs text-gray-600 italic leading-relaxed">
            These core elements are automatically included in all generated content
          </div>
        </div>
      </div>

      {/* Main Settings Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <div className="space-y-10">
            {/* Tone Slider */}
            <div>
              <label className="block">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-5 gap-3">
                  <span className="text-gray-900 text-xl md:text-2xl font-semibold">Brand Tone</span>
                  <span className="text-xs font-medium text-purple-700 bg-purple-100 px-4 py-2 rounded-lg uppercase tracking-wider border border-purple-200">
                    {getSliderLabel("tone", state.brandSettings.tone)}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500 font-medium min-w-[80px] uppercase tracking-wider">
                    Wacky
                  </span>
                  <div className="flex-1 relative">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={state.brandSettings.tone}
                      onChange={(e) => updateBrandSetting("tone", parseInt(e.target.value))}
                      className="slider-purple w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 
                        [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                        [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-purple-600
                        [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                        [&::-webkit-slider-thumb]:ring-4 [&::-webkit-slider-thumb]:ring-purple-100
                        [&::-moz-range-thumb]:w-6 [&::-moz-range-thumb]:h-6 [&::-moz-range-thumb]:bg-white
                        [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:border-4
                        [&::-moz-range-thumb]:border-purple-600 [&::-moz-range-thumb]:cursor-pointer"
                      style={{
                        background: `linear-gradient(to right, #635BFF 0%, #635BFF ${state.brandSettings.tone}%, #E5E7EB ${state.brandSettings.tone}%, #E5E7EB 100%)`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 font-medium min-w-[80px] text-right uppercase tracking-wider">
                    Formal
                  </span>
                </div>
                <div className="mt-4 text-xs text-gray-600 bg-gray-50 rounded-lg p-3 border border-gray-200">
                  {state.brandSettings.tone < 30 && "💬 Playful, meme-friendly, irreverent"}
                  {state.brandSettings.tone >= 30 && state.brandSettings.tone < 70 && "🎯 Conversational yet professional"}
                  {state.brandSettings.tone >= 70 && "👔 Executive-level formality"}
                </div>
              </label>
            </div>

            {/* Pithiness Slider */}
            <div>
              <label className="block">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-5 gap-3">
                  <span className="text-gray-900 text-xl md:text-2xl font-semibold">Writing Style</span>
                  <span className="text-xs font-medium text-blue-700 bg-blue-100 px-4 py-2 rounded-lg uppercase tracking-wider border border-blue-200">
                    {getSliderLabel("pithiness", state.brandSettings.pithiness)}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500 font-medium min-w-[80px] uppercase tracking-wider">
                    Punchy
                  </span>
                  <div className="flex-1 relative">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={state.brandSettings.pithiness}
                      onChange={(e) => updateBrandSetting("pithiness", parseInt(e.target.value))}
                      className="slider-blue w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 
                        [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                        [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-blue-600
                        [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                        [&::-webkit-slider-thumb]:ring-4 [&::-webkit-slider-thumb]:ring-blue-100
                        [&::-moz-range-thumb]:w-6 [&::-moz-range-thumb]:h-6 [&::-moz-range-thumb]:bg-white
                        [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:border-4
                        [&::-moz-range-thumb]:border-blue-600 [&::-moz-range-thumb]:cursor-pointer"
                      style={{
                        background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${state.brandSettings.pithiness}%, #E5E7EB ${state.brandSettings.pithiness}%, #E5E7EB 100%)`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 font-medium min-w-[80px] text-right uppercase tracking-wider">
                    Baroque
                  </span>
                </div>
                <div className="mt-4 text-xs text-gray-600 bg-gray-50 rounded-lg p-3 border border-gray-200">
                  {state.brandSettings.pithiness < 30 && "⚡ Short, punchy sentences"}
                  {state.brandSettings.pithiness >= 30 && state.brandSettings.pithiness < 70 && "⚖️ Balanced detail and brevity"}
                  {state.brandSettings.pithiness >= 70 && "📚 Rich, elaborate storytelling"}
                </div>
              </label>
            </div>

            {/* Jargon Slider */}
            <div>
              <label className="block">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-5 gap-3">
                  <span className="text-gray-900 text-xl md:text-2xl font-semibold">Language Level</span>
                  <span className="text-xs font-medium text-green-700 bg-green-100 px-4 py-2 rounded-lg uppercase tracking-wider border border-green-200">
                    {getSliderLabel("jargon", state.brandSettings.jargon)}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-gray-500 font-medium min-w-[80px] uppercase tracking-wider">
                    Plain
                  </span>
                  <div className="flex-1 relative">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={state.brandSettings.jargon}
                      onChange={(e) => updateBrandSetting("jargon", parseInt(e.target.value))}
                      className="slider-green w-full h-2 bg-gray-200 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-6 [&::-webkit-slider-thumb]:h-6 
                        [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                        [&::-webkit-slider-thumb]:border-4 [&::-webkit-slider-thumb]:border-green-600
                        [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                        [&::-webkit-slider-thumb]:ring-4 [&::-webkit-slider-thumb]:ring-green-100
                        [&::-moz-range-thumb]:w-6 [&::-moz-range-thumb]:h-6 [&::-moz-range-thumb]:bg-white
                        [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:border-4
                        [&::-moz-range-thumb]:border-green-600 [&::-moz-range-thumb]:cursor-pointer"
                      style={{
                        background: `linear-gradient(to right, #10B981 0%, #10B981 ${state.brandSettings.jargon}%, #E5E7EB ${state.brandSettings.jargon}%, #E5E7EB 100%)`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 font-medium min-w-[80px] text-right uppercase tracking-wider">
                    VC-Speak
                  </span>
                </div>
                <div className="mt-4 text-xs text-gray-600 bg-gray-50 rounded-lg p-3 border border-gray-200">
                  {state.brandSettings.jargon < 30 && "🗣️ Simple, accessible language"}
                  {state.brandSettings.jargon >= 30 && state.brandSettings.jargon < 70 && "💼 Moderate business terminology"}
                  {state.brandSettings.jargon >= 70 && "🚀 Heavy startup/VC buzzwords"}
                </div>
              </label>
            </div>

            {/* Custom Brand Additions */}
            <div>
              <label className="block">
                <div className="mb-4">
                  <span className="text-gray-900 text-xl md:text-2xl font-semibold">
                    Custom Brand Additions
                  </span>
                  <span className="text-xs text-gray-500 ml-3 font-medium uppercase tracking-wider">(Optional)</span>
                </div>
                <textarea
                  value={state.brandSettings.custom}
                  onChange={(e) => updateBrandSetting("custom", e.target.value)}
                  placeholder="Add any specific brand guidelines, themes, or messaging you want to emphasize..."
                  className="w-full p-5 bg-gray-50 border border-gray-300 rounded-lg 
                    focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                    transition-all duration-300 min-h-[140px] text-sm text-gray-900 
                    placeholder:text-gray-500 resize-none"
                  maxLength={500}
                />
                <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs">
                  <span className="text-gray-500">
                    Example: "Always emphasize mindfulness" or "Use humor when appropriate"
                  </span>
                  <span className="text-gray-400 font-medium">
                    {state.brandSettings.custom.length}/500
                  </span>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Preview Box */}
      <div className="bg-gradient-to-br from-gray-50 to-slate-50 rounded-xl border border-gray-200 overflow-hidden">
        <div className="p-8 md:p-10">
          <h4 className="text-gray-900 mb-5 flex items-center gap-3 text-xl font-semibold">
            <span className="text-2xl">✦</span>
            Voice Preview
          </h4>
          <div className="text-sm text-gray-700 space-y-3 leading-relaxed">
            <p className="flex flex-wrap gap-x-4 gap-y-2">
              <span>
                <strong className="text-purple-700 font-semibold">Tone:</strong> {getSliderLabel("tone", state.brandSettings.tone)}
              </span>
              <span className="text-gray-400">•</span>
              <span>
                <strong className="text-purple-700 font-semibold">Style:</strong> {getSliderLabel("pithiness", state.brandSettings.pithiness)}
              </span>
              <span className="text-gray-400">•</span>
              <span>
                <strong className="text-purple-700 font-semibold">Language:</strong> {getSliderLabel("jargon", state.brandSettings.jargon)}
              </span>
            </p>
            {state.brandSettings.custom && (
              <p className="pt-3 border-t border-gray-200">
                <strong className="text-purple-700 font-semibold">Custom:</strong> {state.brandSettings.custom}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end">
        <button
          onClick={handleContinue}
          className="w-full sm:w-auto px-12 py-4 text-white rounded-lg font-medium text-sm
            shadow-lg hover:shadow-xl transition-all duration-300 
            flex items-center justify-center gap-3"
          style={{
            background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
          }}
        >
          Continue to Inspiration
          <span className="text-lg">→</span>
        </button>
      </div>
    </div>
  );
}