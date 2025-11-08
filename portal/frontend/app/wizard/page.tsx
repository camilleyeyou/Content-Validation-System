// portal/frontend/app/wizard/page.tsx
"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import Step1Brand from "./steps/Step1Brand";
import Step2Inspiration from "./steps/Step2Inspiration";
import Step3Style from "./steps/Step3Style";
import Step4Persona from "./steps/Step4Persona";
import Step5Finalize from "./steps/Step5Finalize";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://localhost:8001";

export type WizardState = {
  currentStep: number;
  brandSettings: {
    tone: number;
    pithiness: number;
    jargon: number;
    custom: string;
  };
  inspirationSources?: any;
  inspirationSelections: Array<{
    type: string;
    selected_id: string;
    preview?: any;
  }>;
  length: string;
  styleFlags: string[];
  buyerPersona?: {
    title: string;
    company_size: string;
    sector: string;
    region: string;
    goals: string[];
    risk_tolerance: string;
    decision_criteria: string[];
    personality: string;
    tone_resonance: string;
  };
  generatedPost?: any;
};

export default function WizardPage() {
  const [state, setState] = useState<WizardState>({
    currentStep: 1,
    brandSettings: { tone: 50, pithiness: 50, jargon: 30, custom: "" },
    inspirationSelections: [],
    length: "medium",
    styleFlags: [],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load brand defaults on mount
  useEffect(() => {
    loadBrandDefaults();
  }, []);

  async function loadBrandDefaults() {
    try {
      const response = await fetch(`${API_BASE}/api/wizard/brand-defaults`);
      const data = await response.json();
      
      if (data.ok && data.default_sliders) {
        setState(prev => ({
          ...prev,
          brandSettings: {
            ...prev.brandSettings,
            tone: data.default_sliders.tone_slider,
            pithiness: data.default_sliders.pithiness_slider,
            jargon: data.default_sliders.jargon_slider,
          }
        }));
      }
    } catch (e) {
      console.error("Failed to load brand defaults:", e);
    }
  }

  const nextStep = () => {
    if (state.currentStep < 5) {
      setState(prev => ({ ...prev, currentStep: prev.currentStep + 1 }));
      window.scrollTo(0, 0);
    }
  };

  const prevStep = () => {
    if (state.currentStep > 1) {
      setState(prev => ({ ...prev, currentStep: prev.currentStep - 1 }));
      window.scrollTo(0, 0);
    }
  };

  const goToStep = (step: number) => {
    if (step >= 1 && step <= 5) {
      setState(prev => ({ ...prev, currentStep: step }));
      window.scrollTo(0, 0);
    }
  };

  return (
    <main className="min-h-screen bg-black" style={{ background: 'linear-gradient(to bottom, #000000 0%, #0a0a0a 50%, #000000 100%)' }}>
      <div className="max-w-[1400px] mx-auto px-6 md:px-8 py-12 md:py-16">
        {/* Header */}
        <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
          <div className="p-8 md:p-10">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-center gap-5">
                <div className="w-16 h-16 bg-gradient-to-br from-[#d4af37] via-[#f4e4c1] to-[#d4af37] rounded-sm flex items-center justify-center shadow-lg flex-shrink-0">
                  <span className="text-black text-3xl font-serif font-bold">✨</span>
                </div>
                <div>
                  <h1 className="text-2xl md:text-3xl font-serif font-light text-white tracking-wide">
                    Content Creation Wizard
                  </h1>
                  <p className="text-sm text-gray-400 mt-1 font-light leading-relaxed">
                    Guided creation for perfectly tailored LinkedIn posts
                  </p>
                </div>
              </div>
              <Link
                href="/"
                className="px-6 py-3 bg-white/5 hover:bg-white/10 text-white rounded-sm text-sm font-light uppercase tracking-wider border border-white/10 hover:border-[#d4af37]/30 transition-all duration-300 inline-flex items-center justify-center gap-2"
              >
                ← Back to Dashboard
              </Link>
            </div>
          </div>
        </div>

        {/* Stepper */}
        <StepIndicator currentStep={state.currentStep} onStepClick={goToStep} />

        {/* Error Display */}
        {error && (
          <div className="bg-red-900/20 backdrop-blur-sm rounded-sm border border-red-500/30 shadow-2xl overflow-hidden mb-8">
            <div className="p-6 md:p-8">
              <div className="flex items-start gap-3">
                <span className="text-2xl">❌</span>
                <div>
                  <div className="font-serif text-red-300 text-lg mb-1 font-light">Error</div>
                  <div className="text-sm text-red-400 font-light leading-relaxed">{error}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step Content - No wrapper card needed as steps have their own backgrounds */}
        <div>
          {state.currentStep === 1 && (
            <Step1Brand
              state={state}
              setState={setState}
              onNext={nextStep}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
            />
          )}
          {state.currentStep === 2 && (
            <Step2Inspiration
              state={state}
              setState={setState}
              onNext={nextStep}
              onBack={prevStep}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
            />
          )}
          {state.currentStep === 3 && (
            <Step3Style
              state={state}
              setState={setState}
              onNext={nextStep}
              onBack={prevStep}
            />
          )}
          {state.currentStep === 4 && (
            <Step4Persona
              state={state}
              setState={setState}
              onNext={nextStep}
              onBack={prevStep}
            />
          )}
          {state.currentStep === 5 && (
            <Step5Finalize
              state={state}
              setState={setState}
              onBack={prevStep}
              loading={loading}
              setLoading={setLoading}
              setError={setError}
            />
          )}
        </div>

        {/* Help Text */}
        <div className="mt-8 text-center text-xs text-gray-600 font-light uppercase tracking-widest">
          💡 Tip: Click on any completed step above to go back and make changes
        </div>
      </div>
    </main>
  );
}

// Luxury Stepper Component
function StepIndicator({ currentStep, onStepClick }: { currentStep: number; onStepClick: (step: number) => void }) {
  const steps = [
    { num: 1, name: "Brand", icon: "I" },
    { num: 2, name: "Inspiration", icon: "II" },
    { num: 3, name: "Style", icon: "III" },
    { num: 4, name: "Persona", icon: "IV" },
    { num: 5, name: "Generate", icon: "V" },
  ];

  return (
    <div className="bg-black/40 backdrop-blur-sm rounded-sm border border-[#d4af37]/20 shadow-2xl overflow-hidden mb-8">
      <div className="p-6 md:p-8">
        <div className="flex items-center justify-between gap-2 md:gap-4">
          {steps.map((step, idx) => (
            <div key={step.num} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                {/* Step Circle */}
                <button
                  onClick={() => step.num < currentStep ? onStepClick(step.num) : null}
                  disabled={step.num > currentStep}
                  className={`
                    relative w-10 h-10 md:w-12 md:h-12 rounded-sm border-2 flex items-center justify-center 
                    font-serif text-sm md:text-base transition-all duration-300
                    ${step.num === currentStep
                      ? "bg-[#d4af37] border-[#d4af37] text-black shadow-lg shadow-[#d4af37]/30 scale-110"
                      : step.num < currentStep
                      ? "bg-emerald-500/20 border-emerald-500/50 text-emerald-400 cursor-pointer hover:scale-105 hover:bg-emerald-500/30"
                      : "bg-black/40 border-white/20 text-gray-600 cursor-not-allowed"
                    }
                  `}
                >
                  {step.num < currentStep ? "✓" : step.icon}
                </button>
                
                {/* Step Label */}
                <div className="mt-2 text-xs md:text-sm font-light text-center">
                  <span
                    className={`transition-colors duration-300 ${
                      step.num === currentStep
                        ? "text-[#d4af37]"
                        : step.num < currentStep
                        ? "text-emerald-400"
                        : "text-gray-600"
                    }`}
                  >
                    {step.name}
                  </span>
                </div>
              </div>

              {/* Connector Line */}
              {idx < steps.length - 1 && (
                <div className={`h-0.5 flex-1 mx-2 transition-colors duration-300 ${
                  step.num < currentStep
                    ? "bg-emerald-500/50"
                    : "bg-white/10"
                }`} />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}