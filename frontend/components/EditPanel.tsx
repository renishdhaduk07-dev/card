"use client";

import React from "react";
import type { CardComponent } from "@/types/card";

interface EditPanelProps {
  components: CardComponent[];
  onUpdate: (id: string, newText: string) => void;
}

const LABEL_MAP: Record<string, string> = {
  fullName: "Full Name",
  position: "Position",
  organization_name: "Organization",
  email: "Email",
  phoneNumber: "Phone Number",
  website: "Website",
  fbLink: "Facebook",
  liLink: "LinkedIn",
  igLink: "Instagram",
};

export default function EditPanel({ components, onUpdate }: EditPanelProps) {
  // Only show editable text fields (role_content with text)
  const editableComponents = components.filter(
    (c) =>
      c.type === "role_content" &&
      c.visible &&
      c.cardSide === "front" &&
      c.componentType !== "logo" &&
      c.componentType !== "cardBackground"
  );

  if (editableComponents.length === 0) {
    return (
      <div className="text-center text-sm text-[var(--muted)] py-6">
        No editable fields found.
      </div>
    );
  }

  return (
    <div
      id="edit-panel"
      className="animate-slide-up w-full max-w-md mx-auto bg-[var(--card-bg)] rounded-2xl border border-[var(--border)] p-6"
      style={{
        boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)",
      }}
    >
      <div className="flex items-center gap-2 mb-5">
        <div className="w-8 h-8 rounded-lg bg-[var(--accent-light)] flex items-center justify-center">
          <svg
            className="w-4 h-4 text-[var(--accent)]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10"
            />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-[var(--foreground)]">
          Edit Card Fields
        </h3>
        <span className="ml-auto text-xs text-[var(--muted)]">
          Changes update live
        </span>
      </div>

      <div className="space-y-4">
        {editableComponents.map((comp) => (
          <div key={comp.id}>
            <label
              htmlFor={`edit-${comp.id}`}
              className="block text-xs font-medium text-[var(--muted)] uppercase tracking-wider mb-1.5"
            >
              {LABEL_MAP[comp.componentType] || comp.componentType}
            </label>
            <input
              id={`edit-${comp.id}`}
              type="text"
              value={comp.fallbackText}
              onChange={(e) => onUpdate(comp.id, e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
