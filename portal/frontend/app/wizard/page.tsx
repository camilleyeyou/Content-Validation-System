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
    <main className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50">
      <div className="max-w-5xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="bg-white rounded-2xl border border-purple-200 p-6 shadow-lg mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
                ✨
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Content Creation Wizard</h1>
                <p className="text-sm text-gray-600 mt-1">
                  Guided creation for perfectly tailored LinkedIn posts
                </p>
              </div>
            </div>
            <Link
              href="/"
              className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm font-medium hover:bg-gray-800 transition-all"
            >
              ← Back to Dashboard
            </Link>
          </div>
        </div>

        {/* Stepper */}
        <StepIndicator currentStep={state.currentStep} onStepClick={goToStep} />

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border-2 border-red-200 rounded-xl text-red-900 text-sm">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Step Content */}
        <div className="bg-white rounded-2xl border border-purple-200 shadow-lg overflow-hidden">
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
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>💡 Tip: You can click on any completed step above to go back and make changes</p>
        </div>
      </div>
    </main>
  );
}

// Stepper Component
function StepIndicator({ currentStep, onStepClick }: { currentStep: number; onStepClick: (step: number) => void }) {
  const steps = [
    { num: 1, name: "Brand", icon: "🎨" },
    { num: 2, name: "Inspiration", icon: "💡" },
    { num: 3, name: "Style", icon: "✍️" },
    { num: 4, name: "Persona", icon: "👤" },
    { num: 5, name: "Generate", icon: "🚀" },
  ];

  return (
    <div className="bg-white rounded-2xl border border-purple-200 p-6 shadow-lg mb-6">
      <div className="flex items-center justify-between">
        {steps.map((step, idx) => (
          <div key={step.num} className="flex items-center flex-1">
            {/* Step Circle */}
            <button
              onClick={() => step.num < currentStep ? onStepClick(step.num) : null}
              disabled={step.num > currentStep}
              className={`
                relative w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold transition-all
                ${step.num === currentStep
                  ? "bg-gradient-to-br from-purple-600 to-blue-600 text-white shadow-lg scale-110"
                  : step.num < currentStep
                  ? "bg-green-500 text-white cursor-pointer hover:scale-105"
                  : "bg-gray-200 text-gray-400"
                }
              `}
            >
              {step.num < currentStep ? "✓" : step.icon}
              
              {/* Step Label */}
              <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                <span
                  className={`text-xs font-semibold ${
                    step.num === currentStep
                      ? "text-purple-700"
                      : step.num < currentStep
                      ? "text-green-700"
                      : "text-gray-400"
                  }`}
                >
                  {step.name}
                </span>
              </div>
            </button>

            {/* Connector Line */}
            {idx < steps.length - 1 && (
              <div className="flex-1 h-1 mx-2">
                <div
                  className={`h-full rounded transition-all ${
                    step.num < currentStep ? "bg-green-500" : "bg-gray-200"
                  }`}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}