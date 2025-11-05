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
    <div className="p-8">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Buyer Persona Validation</h2>
        <p className="text-gray-600">
          Optional: Define your target buyer to ensure content resonates with their specific needs
        </p>
      </div>

      {/* Enable/Disable Toggle */}
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border-2 border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900 mb-1">Use Buyer Persona Validation?</h3>
            <p className="text-sm text-gray-600">
              Content will be validated against this specific persona's preferences
            </p>
          </div>
          <button
            onClick={() => handleTogglePersona(!usePersona)}
            className={`relative w-16 h-8 rounded-full transition-all ${
              usePersona ? "bg-green-500" : "bg-gray-300"
            }`}
          >
            <div className={`absolute top-1 w-6 h-6 bg-white rounded-full shadow-md transition-all ${
              usePersona ? "right-1" : "left-1"
            }`} />
          </button>
        </div>
      </div>

      {usePersona && state.buyerPersona && (
        <div className="space-y-6">
          {/* Demographics */}
          <div className="p-6 bg-white border-2 border-gray-200 rounded-xl">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-xl">👤</span>
              Demographics
            </h3>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Job Title *
                </label>
                <input
                  type="text"
                  value={state.buyerPersona.title}
                  onChange={(e) => updatePersona("title", e.target.value)}
                  placeholder="e.g., Marketing Manager, VP of Sales"
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Company Size *
                </label>
                <select
                  value={state.buyerPersona.company_size}
                  onChange={(e) => updatePersona("company_size", e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
                >
                  <option value="Startup">Startup (1-50)</option>
                  <option value="SMB">SMB (51-500)</option>
                  <option value="Enterprise">Enterprise (500+)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Sector *
                </label>
                <select
                  value={state.buyerPersona.sector}
                  onChange={(e) => updatePersona("sector", e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
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
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Region (Optional)
                </label>
                <input
                  type="text"
                  value={state.buyerPersona.region}
                  onChange={(e) => updatePersona("region", e.target.value)}
                  placeholder="e.g., North America, EMEA"
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 focus:ring-2 focus:ring-purple-200 outline-none transition-all"
                />
              </div>
            </div>
          </div>

          {/* Psychographics */}
          <div className="p-6 bg-white border-2 border-gray-200 rounded-xl">
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <span className="text-xl">🧠</span>
              Psychographics
            </h3>

            {/* Goals */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Professional Goals
              </label>
              <div className="space-y-2 mb-2">
                {state.buyerPersona.goals.map((goal, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-blue-50 p-2 rounded">
                    <span className="flex-1 text-sm text-gray-900">{goal}</span>
                    <button
                      onClick={() => removeGoal(idx)}
                      className="text-red-600 hover:text-red-700 font-bold text-sm"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
              <button
                onClick={addGoal}
                className="text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                + Add Goal
              </button>
            </div>

            {/* Decision Criteria */}
            <div className="mb-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Decision Criteria
              </label>
              <div className="space-y-2 mb-2">
                {state.buyerPersona.decision_criteria.map((criteria, idx) => (
                  <div key={idx} className="flex items-center gap-2 bg-purple-50 p-2 rounded">
                    <span className="flex-1 text-sm text-gray-900">{criteria}</span>
                    <button
                      onClick={() => removeCriteria(idx)}
                      className="text-red-600 hover:text-red-700 font-bold text-sm"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
              <button
                onClick={addCriteria}
                className="text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                + Add Criterion
              </button>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Personality
                </label>
                <select
                  value={state.buyerPersona.personality}
                  onChange={(e) => updatePersona("personality", e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                >
                  <option value="Fun">Fun</option>
                  <option value="Angry">Angry</option>
                  <option value="Working on myself">Working on myself</option>
                  <option value="Super Chill">Super Chill</option>
                  <option value="Grinding">Grinding</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Risk Tolerance
                </label>
                <select
                  value={state.buyerPersona.risk_tolerance}
                  onChange={(e) => updatePersona("risk_tolerance", e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                >
                  <option value="Conservative">Conservative</option>
                  <option value="Moderate">Moderate</option>
                  <option value="Aggressive">Aggressive</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Tone Resonance
                </label>
                <select
                  value={state.buyerPersona.tone_resonance}
                  onChange={(e) => updatePersona("tone_resonance", e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:border-purple-500 outline-none"
                >
                  <option value="Analytical">Analytical</option>
                  <option value="Visionary">Visionary</option>
                  <option value="Skeptical">Skeptical</option>
                  <option value="Pragmatic">Pragmatic</option>
                </select>
              </div>
            </div>
          </div>

          {/* Preview */}
          <div className="p-6 bg-gradient-to-r from-green-50 to-blue-50 rounded-xl border-2 border-green-200">
            <h4 className="font-bold text-gray-900 mb-3 flex items-center gap-2">
              <span className="text-xl">👀</span>
              Persona Preview
            </h4>
            <div className="text-sm space-y-1">
              <p className="text-gray-700">
                <strong>{state.buyerPersona.title || "Title not set"}</strong> at {state.buyerPersona.company_size} company in {state.buyerPersona.sector}
              </p>
              <p className="text-gray-600">
                Personality: {state.buyerPersona.personality} • Risk: {state.buyerPersona.risk_tolerance} • Style: {state.buyerPersona.tone_resonance}
              </p>
              {state.buyerPersona.goals.length > 0 && (
                <p className="text-gray-600">Goals: {state.buyerPersona.goals.join(", ")}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {!usePersona && (
        <div className="p-12 text-center bg-gray-50 rounded-xl border-2 border-dashed border-gray-300">
          <div className="text-6xl mb-4">🎯</div>
          <p className="text-gray-600 mb-4">
            Persona validation is disabled. Your content will be validated by our standard personas only.
          </p>
          <button
            onClick={() => handleTogglePersona(true)}
            className="text-purple-600 hover:text-purple-700 font-semibold"
          >
            Enable Persona Validation →
          </button>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-8 border-t border-gray-200">
        <button
          onClick={onBack}
          className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-bold hover:bg-gray-50 transition-all"
        >
          ← Back
        </button>
        <button
          onClick={handleContinue}
          disabled={usePersona && !state.buyerPersona?.title}
          className={`px-8 py-3 rounded-xl font-bold transition-all flex items-center gap-2 ${
            (!usePersona || state.buyerPersona?.title)
              ? "bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl"
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          }`}
        >
          Generate Post
          <span className="text-xl">🚀</span>
        </button>
      </div>
    </div>
  );
}