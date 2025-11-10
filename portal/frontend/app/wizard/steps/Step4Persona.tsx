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
    <div className="space-y-6">
      {/* Header Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <h2 className="text-3xl md:text-4xl font-semibold text-gray-900 mb-3">
            Buyer Persona Validation
          </h2>
          <p className="text-sm md:text-base text-gray-600 leading-relaxed">
            Optional: Define your target buyer to ensure content resonates with their specific needs
          </p>
        </div>
      </div>

      {/* Enable/Disable Toggle Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
        <div className="p-8 md:p-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex-1">
              <h3 className="text-gray-900 text-xl mb-2 font-semibold">
                Use Buyer Persona Validation?
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                Content will be validated against this specific persona's preferences
              </p>
            </div>
            <button
              onClick={() => handleTogglePersona(!usePersona)}
              className={`relative w-20 h-10 rounded-full transition-all duration-300 flex-shrink-0 ${
                usePersona ? "bg-purple-600" : "bg-gray-300"
              }`}
            >
              <div className={`absolute top-1 w-8 h-8 bg-white rounded-full shadow-lg transition-all duration-300 ${
                usePersona ? "right-1" : "left-1"
              }`} />
            </button>
          </div>
        </div>
      </div>

      {usePersona && state.buyerPersona && (
        <div className="space-y-6">
          {/* Demographics Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
            <div className="p-8 md:p-10">
              <h3 className="text-gray-900 text-2xl mb-6 font-semibold flex items-center gap-3">
                <span className="text-2xl">✦</span>
                Demographics
              </h3>
              
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    value={state.buyerPersona.title}
                    onChange={(e) => updatePersona("title", e.target.value)}
                    placeholder="e.g., Marketing Manager, VP of Sales"
                    className="w-full p-4 bg-gray-50 border border-gray-300 rounded-lg 
                      focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                      transition-all duration-300 text-sm text-gray-900 
                      placeholder:text-gray-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                    Company Size *
                  </label>
                  <select
                    value={state.buyerPersona.company_size}
                    onChange={(e) => updatePersona("company_size", e.target.value)}
                    className="w-full p-4 bg-gray-50 border border-gray-300 rounded-lg 
                      focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                      transition-all duration-300 text-sm text-gray-900"
                  >
                    <option value="Startup">Startup (1-50)</option>
                    <option value="SMB">SMB (51-500)</option>
                    <option value="Enterprise">Enterprise (500+)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                    Sector *
                  </label>
                  <select
                    value={state.buyerPersona.sector}
                    onChange={(e) => updatePersona("sector", e.target.value)}
                    className="w-full p-4 bg-gray-50 border border-gray-300 rounded-lg 
                      focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                      transition-all duration-300 text-sm text-gray-900"
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
                  <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                    Region (Optional)
                  </label>
                  <input
                    type="text"
                    value={state.buyerPersona.region}
                    onChange={(e) => updatePersona("region", e.target.value)}
                    placeholder="e.g., North America, EMEA"
                    className="w-full p-4 bg-gray-50 border border-gray-300 rounded-lg 
                      focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                      transition-all duration-300 text-sm text-gray-900 
                      placeholder:text-gray-500"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Psychographics Card */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
            <div className="p-8 md:p-10">
              <h3 className="text-gray-900 text-2xl mb-6 font-semibold flex items-center gap-3">
                <span className="text-2xl">✦</span>
                Psychographics
              </h3>

              {/* Goals */}
              <div className="mb-8">
                <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                  Professional Goals
                </label>
                <div className="space-y-3 mb-4">
                  {state.buyerPersona.goals.map((goal, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-center gap-3 bg-blue-50 p-4 rounded-lg border border-blue-200"
                    >
                      <span className="flex-1 text-sm text-gray-900">{goal}</span>
                      <button
                        onClick={() => removeGoal(idx)}
                        className="text-red-600 hover:text-red-700 font-medium text-sm uppercase tracking-wider transition-colors duration-300"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={addGoal}
                  className="text-sm text-purple-600 hover:text-purple-700 font-medium uppercase tracking-wider transition-colors duration-300"
                >
                  + Add Goal
                </button>
              </div>

              {/* Decision Criteria */}
              <div className="mb-8">
                <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                  Decision Criteria
                </label>
                <div className="space-y-3 mb-4">
                  {state.buyerPersona.decision_criteria.map((criteria, idx) => (
                    <div 
                      key={idx} 
                      className="flex items-center gap-3 bg-purple-50 p-4 rounded-lg border border-purple-200"
                    >
                      <span className="flex-1 text-sm text-gray-900">{criteria}</span>
                      <button
                        onClick={() => removeCriteria(idx)}
                        className="text-red-600 hover:text-red-700 font-medium text-sm uppercase tracking-wider transition-colors duration-300"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
                <button
                  onClick={addCriteria}
                  className="text-sm text-purple-600 hover:text-purple-700 font-medium uppercase tracking-wider transition-colors duration-300"
                >
                  + Add Criterion
                </button>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                    Personality
                  </label>
                  <select
                    value={state.buyerPersona.personality}
                    onChange={(e) => updatePersona("personality", e.target.value)}
                    className="w-full p-4 bg-gray-50 border border-gray-300 rounded-lg 
                      focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                      transition-all duration-300 text-sm text-gray-900"
                  >
                    <option value="Fun">Fun</option>
                    <option value="Angry">Angry</option>
                    <option value="Working on myself">Working on myself</option>
                    <option value="Super Chill">Super Chill</option>
                    <option value="Grinding">Grinding</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                    Risk Tolerance
                  </label>
                  <select
                    value={state.buyerPersona.risk_tolerance}
                    onChange={(e) => updatePersona("risk_tolerance", e.target.value)}
                    className="w-full p-4 bg-gray-50 border border-gray-300 rounded-lg 
                      focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                      transition-all duration-300 text-sm text-gray-900"
                  >
                    <option value="Conservative">Conservative</option>
                    <option value="Moderate">Moderate</option>
                    <option value="Aggressive">Aggressive</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3 uppercase tracking-wider">
                    Tone Resonance
                  </label>
                  <select
                    value={state.buyerPersona.tone_resonance}
                    onChange={(e) => updatePersona("tone_resonance", e.target.value)}
                    className="w-full p-4 bg-gray-50 border border-gray-300 rounded-lg 
                      focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 outline-none 
                      transition-all duration-300 text-sm text-gray-900"
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
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 overflow-hidden">
            <div className="p-8 md:p-10">
              <h4 className="text-gray-900 mb-5 flex items-center gap-3 text-xl font-semibold">
                <span className="text-2xl">✦</span>
                Persona Preview
              </h4>
              <div className="space-y-3 text-sm">
                <p className="text-gray-900 leading-relaxed">
                  <strong className="text-purple-700 font-semibold">{state.buyerPersona.title || "Title not set"}</strong> at {state.buyerPersona.company_size} company in {state.buyerPersona.sector}
                </p>
                <p className="text-gray-700 leading-relaxed">
                  Personality: {state.buyerPersona.personality} • Risk: {state.buyerPersona.risk_tolerance} • Style: {state.buyerPersona.tone_resonance}
                </p>
                {state.buyerPersona.goals.length > 0 && (
                  <p className="text-gray-700 leading-relaxed pt-2 border-t border-green-200">
                    Goals: {state.buyerPersona.goals.join(", ")}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {!usePersona && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200/50 overflow-hidden">
          <div className="p-16 text-center">
            <div className="w-24 h-24 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-6 border border-gray-200">
              <span className="text-5xl">🎯</span>
            </div>
            <h3 className="text-2xl font-semibold text-gray-900 mb-4">
              Persona Validation Disabled
            </h3>
            <p className="text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
              Your content will be validated by our standard personas only.
            </p>
            <button
              onClick={() => handleTogglePersona(true)}
              className="text-purple-600 hover:text-purple-700 font-medium uppercase tracking-wider text-sm transition-colors duration-300"
            >
              Enable Persona Validation →
            </button>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <button
          onClick={onBack}
          className="px-8 py-4 bg-gray-50 hover:bg-gray-100 text-gray-900 rounded-lg font-medium tracking-wider uppercase text-sm border border-gray-200 hover:border-gray-300 transition-all duration-300"
        >
          ← Back
        </button>
        <button
          onClick={handleContinue}
          disabled={usePersona && !state.buyerPersona?.title}
          className={`px-12 py-4 rounded-lg font-medium tracking-wider uppercase text-sm transition-all duration-300 flex items-center justify-center gap-3 ${
            (!usePersona || state.buyerPersona?.title)
              ? "text-white shadow-lg hover:shadow-xl"
              : "bg-gray-100 text-gray-400 cursor-not-allowed border border-gray-200"
          }`}
          style={(!usePersona || state.buyerPersona?.title) ? {
            background: 'linear-gradient(135deg, #635BFF 0%, #4F46E5 100%)',
          } : {}}
        >
          Generate Post
          <span className="text-lg">🚀</span>
        </button>
      </div>
    </div>
  );
}