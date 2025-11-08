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
    <div className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
      <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
        {/* Header Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h2 className="text-3xl md:text-4xl font-serif font-light text-white mb-3 tracking-wide">
              Brand Voice Settings
            </h2>
            <p className="text-sm md:text-base text-gray-400 font-light leading-relaxed">
              Customize how your brand speaks. Use the sliders to find your perfect voice.
            </p>
          </div>
        </div>

        {/* Brand Pillars Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h3 className="font-serif text-white mb-6 flex items-center gap-3 text-xl md:text-2xl font-light tracking-wide">
              <span className="text-2xl">✦</span>
              Jesse A. Eisenbalm Brand Essence
            </h3>
            <div className="grid sm:grid-cols-3 gap-6 md:gap-8 text-sm">
              <div>
                <div className="font-normal text-[#d4af37] mb-2 uppercase tracking-wider text-xs">Product</div>
                <div className="text-gray-300 font-light">Premium business lip balm</div>
              </div>
              <div>
                <div className="font-normal text-[#d4af37] mb-2 uppercase tracking-wider text-xs">Price</div>
                <div className="text-gray-300 font-light">$8.99</div>
              </div>
              <div>
                <div className="font-normal text-[#d4af37] mb-2 uppercase tracking-wider text-xs">Ritual</div>
                <div className="text-gray-300 font-light">Stop, Breathe, Balm</div>
              </div>
            </div>
            <div className="mt-6 text-xs text-gray-500 font-light italic leading-relaxed">
              These core elements are automatically included in all generated content
            </div>
          </div>
        </div>

        {/* Main Settings Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <div className="space-y-10">
              {/* Tone Slider */}
              <div>
                <label className="block">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-5 gap-3">
                    <span className="font-serif text-white text-xl md:text-2xl font-light tracking-wide">Brand Tone</span>
                    <span className="text-xs font-light text-[#d4af37] bg-[#d4af37]/10 px-5 py-2 rounded-sm uppercase tracking-widest border border-[#d4af37]/30">
                      {getSliderLabel("tone", state.brandSettings.tone)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-500 font-light min-w-[70px] uppercase tracking-wider">
                      Wacky
                    </span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={state.brandSettings.tone}
                      onChange={(e) => updateBrandSetting("tone", parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gradient-to-r from-yellow-600/30 via-blue-600/30 to-gray-600/30 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 
                        [&::-webkit-slider-thumb]:bg-[#d4af37] [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                        [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-black
                        [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                        [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:bg-[#d4af37] 
                        [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:border-2 
                        [&::-moz-range-thumb]:border-black [&::-moz-range-thumb]:cursor-pointer"
                    />
                    <span className="text-xs text-gray-500 font-light min-w-[70px] text-right uppercase tracking-wider">
                      Formal
                    </span>
                  </div>
                  <div className="mt-4 text-xs text-gray-400 font-light">
                    {state.brandSettings.tone < 30 && "Playful, meme-friendly, irreverent"}
                    {state.brandSettings.tone >= 30 && state.brandSettings.tone < 70 && "Conversational yet professional"}
                    {state.brandSettings.tone >= 70 && "Executive-level formality"}
                  </div>
                </label>
              </div>

              {/* Pithiness Slider */}
              <div>
                <label className="block">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-5 gap-3">
                    <span className="font-serif text-white text-xl md:text-2xl font-light tracking-wide">Writing Style</span>
                    <span className="text-xs font-light text-blue-300 bg-blue-500/10 px-5 py-2 rounded-sm uppercase tracking-widest border border-blue-500/30">
                      {getSliderLabel("pithiness", state.brandSettings.pithiness)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-500 font-light min-w-[70px] uppercase tracking-wider">
                      Punchy
                    </span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={state.brandSettings.pithiness}
                      onChange={(e) => updateBrandSetting("pithiness", parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gradient-to-r from-red-600/30 via-yellow-600/30 to-purple-600/30 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 
                        [&::-webkit-slider-thumb]:bg-[#d4af37] [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                        [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-black
                        [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                        [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:bg-[#d4af37] 
                        [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:border-2 
                        [&::-moz-range-thumb]:border-black [&::-moz-range-thumb]:cursor-pointer"
                    />
                    <span className="text-xs text-gray-500 font-light min-w-[70px] text-right uppercase tracking-wider">
                      Baroque
                    </span>
                  </div>
                  <div className="mt-4 text-xs text-gray-400 font-light">
                    {state.brandSettings.pithiness < 30 && "Short, punchy sentences"}
                    {state.brandSettings.pithiness >= 30 && state.brandSettings.pithiness < 70 && "Balanced detail and brevity"}
                    {state.brandSettings.pithiness >= 70 && "Rich, elaborate storytelling"}
                  </div>
                </label>
              </div>

              {/* Jargon Slider */}
              <div>
                <label className="block">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-5 gap-3">
                    <span className="font-serif text-white text-xl md:text-2xl font-light tracking-wide">Language Level</span>
                    <span className="text-xs font-light text-emerald-300 bg-emerald-500/10 px-5 py-2 rounded-sm uppercase tracking-widest border border-emerald-500/30">
                      {getSliderLabel("jargon", state.brandSettings.jargon)}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-500 font-light min-w-[70px] uppercase tracking-wider">
                      Plain
                    </span>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={state.brandSettings.jargon}
                      onChange={(e) => updateBrandSetting("jargon", parseInt(e.target.value))}
                      className="flex-1 h-2 bg-gradient-to-r from-green-600/30 via-blue-600/30 to-indigo-600/30 rounded-full appearance-none cursor-pointer
                        [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5 
                        [&::-webkit-slider-thumb]:bg-[#d4af37] [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:shadow-lg
                        [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-black
                        [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:hover:scale-110 [&::-webkit-slider-thumb]:transition-transform
                        [&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:bg-[#d4af37] 
                        [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:border-2 
                        [&::-moz-range-thumb]:border-black [&::-moz-range-thumb]:cursor-pointer"
                    />
                    <span className="text-xs text-gray-500 font-light min-w-[70px] text-right uppercase tracking-wider">
                      VC-Speak
                    </span>
                  </div>
                  <div className="mt-4 text-xs text-gray-400 font-light">
                    {state.brandSettings.jargon < 30 && "Simple, accessible language"}
                    {state.brandSettings.jargon >= 30 && state.brandSettings.jargon < 70 && "Moderate business terminology"}
                    {state.brandSettings.jargon >= 70 && "Heavy startup/VC buzzwords"}
                  </div>
                </label>
              </div>

              {/* Custom Brand Additions */}
              <div>
                <label className="block">
                  <div className="mb-4">
                    <span className="font-serif text-white text-xl md:text-2xl font-light tracking-wide">
                      Custom Brand Additions
                    </span>
                    <span className="text-xs text-gray-500 ml-3 font-light uppercase tracking-wider">(Optional)</span>
                  </div>
                  <textarea
                    value={state.brandSettings.custom}
                    onChange={(e) => updateBrandSetting("custom", e.target.value)}
                    placeholder="Add any specific brand guidelines, themes, or messaging you want to emphasize..."
                    className="w-full p-5 bg-black/40 border border-white/10 rounded-sm 
                      focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                      transition-all duration-300 min-h-[140px] text-sm text-gray-200 
                      font-light placeholder:text-gray-600 resize-none"
                    maxLength={500}
                  />
                  <div className="mt-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs">
                    <span className="text-gray-500 font-light">
                      Example: "Always emphasize mindfulness" or "Use humor when appropriate"
                    </span>
                    <span className="text-gray-600 font-light">
                      {state.brandSettings.custom.length}/500
                    </span>
                  </div>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Preview Box */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h4 className="font-serif text-white mb-5 flex items-center gap-3 text-xl font-light tracking-wide">
              <span className="text-2xl">✦</span>
              Voice Preview
            </h4>
            <div className="text-sm text-gray-300 space-y-3 font-light leading-relaxed">
              <p className="flex flex-wrap gap-x-4 gap-y-2">
                <span>
                  <strong className="text-[#d4af37] font-normal">Tone:</strong> {getSliderLabel("tone", state.brandSettings.tone)}
                </span>
                <span className="text-gray-600">•</span>
                <span>
                  <strong className="text-[#d4af37] font-normal">Style:</strong> {getSliderLabel("pithiness", state.brandSettings.pithiness)}
                </span>
                <span className="text-gray-600">•</span>
                <span>
                  <strong className="text-[#d4af37] font-normal">Language:</strong> {getSliderLabel("jargon", state.brandSettings.jargon)}
                </span>
              </p>
              {state.brandSettings.custom && (
                <p className="pt-3 border-t border-white/10">
                  <strong className="text-[#d4af37] font-normal">Custom:</strong> {state.brandSettings.custom}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end">
          <button
            onClick={handleContinue}
            className="w-full sm:w-auto px-12 py-4 bg-gradient-to-br from-[#d4af37] to-[#b8941f] 
              text-black rounded-sm font-light tracking-wider uppercase text-sm
              hover:shadow-2xl hover:shadow-[#d4af37]/20 transition-all duration-500 
              flex items-center justify-center gap-3"
          >
            Continue to Inspiration
            <span className="text-lg">→</span>
          </button>
        </div>
      </div>
    </div>
  );
}