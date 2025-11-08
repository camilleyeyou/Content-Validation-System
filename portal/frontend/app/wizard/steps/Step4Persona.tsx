// portal/frontend/app/wizard/steps/Step4Persona.tsx
"use client";
import { useState } from "react";
import { WizardState } from "../page";

type Props = {
  state: WizardState;
  setState: React.Dispatch<React.SetStateAction<WizardState>>;
  onNext: () => void;
  onBack: () => void;
};

export default function Step4Persona({ state, setState, onNext, onBack }: Props) {
  const [usePersona, setUsePersona] = useState(!!state.buyerPersona);
  
  const updatePersona = (key: string, value: any) => {
    setState(prev => ({
      ...prev,
      buyerPersona: {
        ...prev.buyerPersona!,
        [key]: value
      }
    }));
  };

  const addGoal = () => {
    const newGoal = prompt("Enter a professional goal:");
    if (newGoal?.trim()) {
      const goals = state.buyerPersona?.goals || [];
      updatePersona("goals", [...goals, newGoal.trim()]);
    }
  };

  const removeGoal = (index: number) => {
    const goals = state.buyerPersona?.goals || [];
    updatePersona("goals", goals.filter((_, i) => i !== index));
  };

  const addCriteria = () => {
    const newCriteria = prompt("Enter a decision criterion:");
    if (newCriteria?.trim()) {
      const criteria = state.buyerPersona?.decision_criteria || [];
      updatePersona("decision_criteria", [...criteria, newCriteria.trim()]);
    }
  };

  const removeCriteria = (index: number) => {
    const criteria = state.buyerPersona?.decision_criteria || [];
    updatePersona("decision_criteria", criteria.filter((_, i) => i !== index));
  };

  const handleTogglePersona = (enabled: boolean) => {
    setUsePersona(enabled);
    if (enabled && !state.buyerPersona) {
      // Initialize with defaults
      setState(prev => ({
        ...prev,
        buyerPersona: {
          title: "",
          company_size: "Enterprise",
          sector: "Technology",
          region: "",
          goals: [],
          risk_tolerance: "Moderate",
          decision_criteria: [],
          personality: "Grinding",
          tone_resonance: "Analytical"
        }
      }));
    } else if (!enabled) {
      setState(prev => ({ ...prev, buyerPersona: undefined }));
    }
  };

  const handleContinue = () => {
    if (!usePersona) {
      setState(prev => ({ ...prev, buyerPersona: undefined }));
    }
    onNext();
  };

  return (
    <div className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
      <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
        {/* Header Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <h2 className="text-3xl md:text-4xl font-serif font-light text-white mb-3 tracking-wide">
              Buyer Persona Validation
            </h2>
            <p className="text-sm md:text-base text-gray-400 font-light leading-relaxed">
              Optional: Define your target buyer to ensure content resonates with their specific needs
            </p>
          </div>
        </div>

        {/* Enable/Disable Toggle Card */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex-1">
                <h3 className="font-serif text-white text-xl mb-2 font-light tracking-wide">
                  Use Buyer Persona Validation?
                </h3>
                <p className="text-sm text-gray-400 font-light leading-relaxed">
                  Content will be validated against this specific persona's preferences
                </p>
              </div>
              <button
                onClick={() => handleTogglePersona(!usePersona)}
                className={`relative w-20 h-10 rounded-sm transition-all duration-300 flex-shrink-0 ${
                  usePersona ? "bg-[#d4af37]" : "bg-white/20"
                }`}
              >
                <div className={`absolute top-1 w-8 h-8 bg-black rounded-sm shadow-lg transition-all duration-300 ${
                  usePersona ? "right-1" : "left-1"
                }`} />
              </button>
            </div>
          </div>
        </div>

        {usePersona && state.buyerPersona && (
          <div className="space-y-8">
            {/* Demographics Card */}
            <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
              <div className="p-8 md:p-10">
                <h3 className="font-serif text-white text-2xl mb-6 font-light tracking-wide flex items-center gap-3">
                  <span className="text-2xl">✦</span>
                  Demographics
                </h3>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                      Job Title *
                    </label>
                    <input
                      type="text"
                      value={state.buyerPersona.title}
                      onChange={(e) => updatePersona("title", e.target.value)}
                      placeholder="e.g., Marketing Manager, VP of Sales"
                      className="w-full p-4 bg-black/40 border border-white/10 rounded-sm 
                        focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                        transition-all duration-300 text-sm text-gray-200 font-light 
                        placeholder:text-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                      Company Size *
                    </label>
                    <select
                      value={state.buyerPersona.company_size}
                      onChange={(e) => updatePersona("company_size", e.target.value)}
                      className="w-full p-4 bg-black/40 border border-white/10 rounded-sm 
                        focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                        transition-all duration-300 text-sm text-gray-200 font-light"
                    >
                      <option value="Startup">Startup (1-50)</option>
                      <option value="SMB">SMB (51-500)</option>
                      <option value="Enterprise">Enterprise (500+)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                      Sector *
                    </label>
                    <select
                      value={state.buyerPersona.sector}
                      onChange={(e) => updatePersona("sector", e.target.value)}
                      className="w-full p-4 bg-black/40 border border-white/10 rounded-sm 
                        focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                        transition-all duration-300 text-sm text-gray-200 font-light"
                    >
                      <option value="Technology">Technology</option>
                      <option value="Finance">Finance</option>
                      <option value="Healthcare">Healthcare</option>
                      <option value="Retail">Retail</option>
                      <option value="Manufacturing">Manufacturing</option>
                      <option value="Professional Services">Professional Services</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                      Region (Optional)
                    </label>
                    <input
                      type="text"
                      value={state.buyerPersona.region}
                      onChange={(e) => updatePersona("region", e.target.value)}
                      placeholder="e.g., North America, EMEA"
                      className="w-full p-4 bg-black/40 border border-white/10 rounded-sm 
                        focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                        transition-all duration-300 text-sm text-gray-200 font-light 
                        placeholder:text-gray-600"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Psychographics Card */}
            <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden">
              <div className="p-8 md:p-10">
                <h3 className="font-serif text-white text-2xl mb-6 font-light tracking-wide flex items-center gap-3">
                  <span className="text-2xl">✦</span>
                  Psychographics
                </h3>

                {/* Goals */}
                <div className="mb-8">
                  <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                    Professional Goals
                  </label>
                  <div className="space-y-3 mb-4">
                    {state.buyerPersona.goals.map((goal, idx) => (
                      <div 
                        key={idx} 
                        className="flex items-center gap-3 bg-blue-500/10 p-4 rounded-sm border border-blue-500/30"
                      >
                        <span className="flex-1 text-sm text-gray-200 font-light">{goal}</span>
                        <button
                          onClick={() => removeGoal(idx)}
                          className="text-red-400 hover:text-red-300 font-light text-sm uppercase tracking-wider transition-colors duration-300"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={addGoal}
                    className="text-sm text-[#d4af37] hover:text-[#f4e4c1] font-light uppercase tracking-wider transition-colors duration-300"
                  >
                    + Add Goal
                  </button>
                </div>

                {/* Decision Criteria */}
                <div className="mb-8">
                  <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                    Decision Criteria
                  </label>
                  <div className="space-y-3 mb-4">
                    {state.buyerPersona.decision_criteria.map((criteria, idx) => (
                      <div 
                        key={idx} 
                        className="flex items-center gap-3 bg-purple-500/10 p-4 rounded-sm border border-purple-500/30"
                      >
                        <span className="flex-1 text-sm text-gray-200 font-light">{criteria}</span>
                        <button
                          onClick={() => removeCriteria(idx)}
                          className="text-red-400 hover:text-red-300 font-light text-sm uppercase tracking-wider transition-colors duration-300"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                  <button
                    onClick={addCriteria}
                    className="text-sm text-[#d4af37] hover:text-[#f4e4c1] font-light uppercase tracking-wider transition-colors duration-300"
                  >
                    + Add Criterion
                  </button>
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                      Personality
                    </label>
                    <select
                      value={state.buyerPersona.personality}
                      onChange={(e) => updatePersona("personality", e.target.value)}
                      className="w-full p-4 bg-black/40 border border-white/10 rounded-sm 
                        focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                        transition-all duration-300 text-sm text-gray-200 font-light"
                    >
                      <option value="Fun">Fun</option>
                      <option value="Angry">Angry</option>
                      <option value="Working on myself">Working on myself</option>
                      <option value="Super Chill">Super Chill</option>
                      <option value="Grinding">Grinding</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                      Risk Tolerance
                    </label>
                    <select
                      value={state.buyerPersona.risk_tolerance}
                      onChange={(e) => updatePersona("risk_tolerance", e.target.value)}
                      className="w-full p-4 bg-black/40 border border-white/10 rounded-sm 
                        focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                        transition-all duration-300 text-sm text-gray-200 font-light"
                    >
                      <option value="Conservative">Conservative</option>
                      <option value="Moderate">Moderate</option>
                      <option value="Aggressive">Aggressive</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-light text-gray-400 mb-3 uppercase tracking-wider">
                      Tone Resonance
                    </label>
                    <select
                      value={state.buyerPersona.tone_resonance}
                      onChange={(e) => updatePersona("tone_resonance", e.target.value)}
                      className="w-full p-4 bg-black/40 border border-white/10 rounded-sm 
                        focus:border-[#d4af37]/50 focus:ring-1 focus:ring-[#d4af37]/30 outline-none 
                        transition-all duration-300 text-sm text-gray-200 font-light"
                    >
                      <option value="Analytical">Analytical</option>
                      <option value="Visionary">Visionary</option>
                      <option value="Skeptical">Skeptical</option>
                      <option value="Pragmatic">Pragmatic</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Preview Card */}
            <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-emerald-500/30 shadow-2xl overflow-hidden">
              <div className="p-8 md:p-10">
                <h4 className="font-serif text-white mb-5 flex items-center gap-3 text-xl font-light tracking-wide">
                  <span className="text-2xl">✦</span>
                  Persona Preview
                </h4>
                <div className="space-y-3 text-sm font-light">
                  <p className="text-gray-200 leading-relaxed">
                    <strong className="text-[#d4af37] font-normal">{state.buyerPersona.title || "Title not set"}</strong> at {state.buyerPersona.company_size} company in {state.buyerPersona.sector}
                  </p>
                  <p className="text-gray-400 leading-relaxed">
                    Personality: {state.buyerPersona.personality} • Risk: {state.buyerPersona.risk_tolerance} • Style: {state.buyerPersona.tone_resonance}
                  </p>
                  {state.buyerPersona.goals.length > 0 && (
                    <p className="text-gray-400 leading-relaxed pt-2 border-t border-white/10">
                      Goals: {state.buyerPersona.goals.join(", ")}
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {!usePersona && (
          <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-white/10 shadow-2xl overflow-hidden">
            <div className="p-16 text-center">
              <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-white/10">
                <span className="text-5xl">🎯</span>
              </div>
              <h3 className="text-2xl font-serif font-light text-white mb-4 tracking-wide">
                Persona Validation Disabled
              </h3>
              <p className="text-gray-400 font-light mb-8 max-w-md mx-auto leading-relaxed">
                Your content will be validated by our standard personas only.
              </p>
              <button
                onClick={() => handleTogglePersona(true)}
                className="text-[#d4af37] hover:text-[#f4e4c1] font-light uppercase tracking-wider text-sm transition-colors duration-300"
              >
                Enable Persona Validation →
              </button>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mt-8">
          <button
            onClick={onBack}
            className="px-8 py-4 bg-white/5 hover:bg-white/10 text-white rounded-sm font-light tracking-wider uppercase text-sm border border-white/10 hover:border-white/20 transition-all duration-300"
          >
            ← Back
          </button>
          <button
            onClick={handleContinue}
            disabled={usePersona && !state.buyerPersona?.title}
            className={`px-12 py-4 rounded-sm font-light tracking-wider uppercase text-sm transition-all duration-500 flex items-center justify-center gap-3 ${
              (!usePersona || state.buyerPersona?.title)
                ? "bg-gradient-to-br from-[#d4af37] to-[#b8941f] text-black hover:shadow-2xl hover:shadow-[#d4af37]/20"
                : "bg-white/5 text-gray-600 cursor-not-allowed border border-white/10"
            }`}
          >
            Generate Post
            <span className="text-lg">🚀</span>
          </button>
        </div>
      </div>
    </div>
  );
}