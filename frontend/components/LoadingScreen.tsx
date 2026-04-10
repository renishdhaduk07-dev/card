"use client";

import React, { useEffect, useState } from "react";

const STEPS = [
  { id: "planner",   label: "Planner",            icon: "📋" },
  { id: "research",  label: "Research",            icon: "🔍" },
  { id: "enrichment",label: "Enrichment",          icon: "✨" },
  { id: "template",  label: "Template Selection",  icon: "🎨" },
  { id: "fill",      label: "Fill",                icon: "📝" },
  { id: "critic",    label: "Critic",              icon: "🧠" },
];

export default function LoadingScreen() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => {
        if (prev < STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="animate-fade-in flex flex-col items-center justify-center px-4 py-20 min-h-[70vh]">
      {/* Spinner */}
      <div className="relative mb-10">
        {/* Outer ring */}
        <div className="w-20 h-20 rounded-full border-[3px] border-[var(--border)]" />
        {/* Spinning arc */}
        <div
          className="absolute inset-0 w-20 h-20 rounded-full border-[3px] border-transparent animate-spin-slow"
          style={{ borderTopColor: "var(--accent)" }}
        />
        {/* Pulse ring */}
        <div className="absolute inset-0 w-20 h-20 rounded-full border-2 border-[var(--accent)] animate-pulse-ring opacity-30" />
        {/* Center icon */}
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="w-7 h-7 text-[var(--accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
          </svg>
        </div>
      </div>

      {/* Text */}
      <h2 className="text-xl font-semibold text-[var(--foreground)] mb-2 text-center">
        AI is analyzing brand and generating your card...
      </h2>
      <p className="text-sm text-[var(--muted)] mb-10">This usually takes 15-30 seconds</p>

      {/* Steps */}
      <div className="w-full max-w-sm space-y-2">
        {STEPS.map((step, i) => {
          const isDone = i < activeStep;
          const isCurrent = i === activeStep;

          return (
            <div
              key={step.id}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-500
                ${isCurrent ? "bg-[var(--accent-light)] animate-step-glow" : ""}
                ${isDone ? "opacity-60" : ""}
                ${!isDone && !isCurrent ? "opacity-30" : ""}
              `}
            >
              {/* Status indicator */}
              <div className="relative flex-shrink-0">
                {isDone ? (
                  <div className="w-6 h-6 rounded-full bg-[var(--success)] flex items-center justify-center">
                    <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    </svg>
                  </div>
                ) : isCurrent ? (
                  <div className="w-6 h-6 rounded-full bg-[var(--accent)] flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-white animate-pulse" />
                  </div>
                ) : (
                  <div className="w-6 h-6 rounded-full border-2 border-[var(--border)] bg-white" />
                )}
              </div>

              {/* Icon + Label */}
              <span className="text-base mr-1">{step.icon}</span>
              <span
                className={`text-sm font-medium ${
                  isCurrent
                    ? "text-[var(--accent)]"
                    : isDone
                    ? "text-[var(--foreground)]"
                    : "text-[var(--muted)]"
                }`}
              >
                {step.label}
              </span>

              {/* Current indicator */}
              {isCurrent && (
                <span className="ml-auto text-xs text-[var(--accent)] font-medium">
                  Running...
                </span>
              )}
              {isDone && (
                <span className="ml-auto text-xs text-[var(--success)] font-medium">
                  Done
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
