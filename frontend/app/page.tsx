"use client";

import React, { useState, useCallback } from "react";
import type { UserData, GenerateResponse, FinalCardJSON } from "@/types/card";
import InputForm from "@/components/InputForm";
import LoadingScreen from "@/components/LoadingScreen";
import CardRenderer from "@/components/CardRenderer";
import ActionButtons from "@/components/ActionButtons";
import EditPanel from "@/components/EditPanel";

type Screen = "input" | "loading" | "result" | "error";

export default function Home() {
  const [screen, setScreen] = useState<Screen>("input");
  const [cardJson, setCardJson] = useState<FinalCardJSON | null>(null);
  const [templateId, setTemplateId] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [toastExiting, setToastExiting] = useState(false);
  const [backendState, setBackendState] = useState<Record<string, any> | null>(null);
  const [rejectedTemplates, setRejectedTemplates] = useState<string[]>([]);

  // ─── Generate card ──────────────────────────────────────
  const handleGenerate = useCallback(async (url: string, userData: UserData) => {
    setScreen("loading");
    setIsEditing(false);
    setErrorMessage("");

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, user_data: userData }),
      });

      const data: GenerateResponse = await res.json();

      if (!data.success || !data.final_card_json) {
        setErrorMessage(data.error || "Card generation failed. Please try again.");
        setScreen("error");
        return;
      }

      setCardJson(data.final_card_json);
      setTemplateId(data.template_id || "unknown");
      setBackendState(data.backend_state || null);
      if (data.template_id) {
        setRejectedTemplates([data.template_id]);
      }
      setScreen("result");
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Network error. Is the backend running?"
      );
      setScreen("error");
    }
  }, []);

  // ─── Edit handler ──────────────────────────────────────
  const handleFieldUpdate = useCallback(
    (componentId: string, newText: string) => {
      if (!cardJson) return;
      setCardJson({
        ...cardJson,
        components: cardJson.components.map((c) =>
          c.id === componentId ? { ...c, fallbackText: newText } : c
        ),
      });
    },
    [cardJson]
  );

  // ─── Accept handler ─────────────────────────────────────
  // Accept handler with JSON download
  const handleAccept = useCallback(() => {
    setShowToast(true);
    setToastExiting(false);
    // Download cardJson as JSON file
    if (cardJson) {
      const jsonStr = JSON.stringify(cardJson, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `business_card.json`;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 0);
    }
    setTimeout(() => {
      setToastExiting(true);
      setTimeout(() => setShowToast(false), 300);
    }, 2500);
  }, [cardJson]);

  // ─── Regenerate ──────────────────────────────────────────
  const handleRegenerate = useCallback(async () => {
    if (!backendState) {
      setScreen("input");
      setCardJson(null);
      setTemplateId("");
      setIsEditing(false);
      setBackendState(null);
      setRejectedTemplates([]);
      return;
    }

    setScreen("loading");
    setIsEditing(false);
    setErrorMessage("");

    try {
      const res = await fetch("/api/regenerate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          backend_state: backendState,
          rejected_templates: rejectedTemplates
        }),
      });

      const data: GenerateResponse = await res.json();

      if (!data.success || !data.final_card_json) {
        setErrorMessage(data.error || "Card regeneration failed. Please try again.");
        setScreen("error");
        return;
      }

      setCardJson(data.final_card_json);
      setTemplateId(data.template_id || "unknown");
      setBackendState(data.backend_state || null);
      
      // Add newly selected template to rejected list for future regenerations
      if (data.template_id) {
        setRejectedTemplates(prev => [...prev, data.template_id]);
      }
      
      setScreen("result");
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : "Network error. Is the backend running?"
      );
      setScreen("error");
    }
  }, [backendState, rejectedTemplates]);

  // ─── Hard Reset (Start Over) ──────────────────────────────
  const handleStartOver = useCallback(() => {
    setScreen("input");
    setCardJson(null);
    setTemplateId("");
    setIsEditing(false);
    setBackendState(null);
    setRejectedTemplates([]);
  }, []);

  return (
    <main className="flex-1 relative">
      {/* ─────────── Input Screen ─────────── */}
      {screen === "input" && <InputForm onSubmit={handleGenerate} />}

      {/* ─────────── Loading Screen ─────────── */}
      {screen === "loading" && <LoadingScreen />}

      {/* ─────────── Error Screen ─────────── */}
      {screen === "error" && (
        <div className="animate-fade-in flex flex-col items-center justify-center px-4 py-20 min-h-[70vh]">
          <div className="w-16 h-16 rounded-2xl bg-red-50 flex items-center justify-center mb-5">
            <svg className="w-8 h-8 text-[var(--error)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-[var(--foreground)] mb-2">
            Something went wrong
          </h2>
          <p className="text-sm text-[var(--muted)] mb-6 text-center max-w-md">
            {errorMessage}
          </p>
          <button
            id="try-again-button"
            onClick={handleStartOver}
            className="px-6 py-2.5 rounded-xl text-sm font-semibold text-white cursor-pointer transition-all duration-200"
            style={{ background: "linear-gradient(135deg, #6366f1, #8b5cf6)" }}
          >
            Try Again
          </button>
        </div>
      )}

      {/* ─────────── Result Screen ─────────── */}
      {screen === "result" && cardJson && (
        <div className="animate-fade-in flex flex-col items-center px-4 py-12">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-50 text-[var(--success)] text-xs font-semibold tracking-wide uppercase mb-6">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            Card Generated
          </div>

          {/* Card hero */}
          <div className="mb-6 w-full max-w-3xl">
            <CardRenderer cardJson={cardJson} />
          </div>

          {/* Template badge */}
          <p className="text-sm text-[var(--muted)] mb-8">
            Template:{" "}
            <span className="font-bold text-[var(--foreground)]">{templateId}</span>
          </p>

          {/* Action buttons */}
          <ActionButtons
            onAccept={handleAccept}
            onEdit={() => setIsEditing((v) => !v)}
            onRegenerate={handleRegenerate}
            isEditing={isEditing}
          />

          {/* Edit panel */}
          {isEditing && (
            <div className="mt-8 w-full">
              <EditPanel
                components={cardJson.components}
                onUpdate={handleFieldUpdate}
              />
            </div>
          )}
        </div>
      )}

      {/* ─────────── Toast ─────────── */}
      {showToast && (
        <div
          className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 px-5 py-3 rounded-xl text-sm font-semibold text-white shadow-lg
            ${toastExiting ? "animate-toast-out" : "animate-toast-in"}`}
          style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}
        >
          <span className="inline-flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
            Card saved!
          </span>
        </div>
      )}
    </main>
  );
}
