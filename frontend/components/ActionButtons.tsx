"use client";

import React from "react";

interface ActionButtonsProps {
  onAccept: () => void;
  onEdit: () => void;
  onRegenerate: () => void;
  isEditing: boolean;
}

export default function ActionButtons({
  onAccept,
  onEdit,
  onRegenerate,
  isEditing,
}: ActionButtonsProps) {
  return (
    <div className="flex flex-wrap items-center justify-center gap-3" id="action-buttons">
      {/* Accept */}
      <button
        id="accept-button"
        onClick={onAccept}
        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold text-white transition-all duration-200 cursor-pointer hover:shadow-lg"
        style={{ background: "linear-gradient(135deg, #10b981, #059669)" }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.background =
            "linear-gradient(135deg, #059669, #047857)")
        }
        onMouseLeave={(e) =>
          (e.currentTarget.style.background =
            "linear-gradient(135deg, #10b981, #059669)")
        }
      >
        <span>✅</span> Accept
      </button>

      {/* Edit */}
      <button
        id="edit-button"
        onClick={onEdit}
        className={`inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer border
          ${
            isEditing
              ? "bg-[var(--accent)] text-white border-[var(--accent)]"
              : "bg-white text-[var(--foreground)] border-[var(--border)] hover:border-[var(--accent)] hover:text-[var(--accent)]"
          }`}
      >
        <span>✏️</span> {isEditing ? "Close Editor" : "Edit"}
      </button>

      {/* Regenerate */}
      <button
        id="regenerate-button"
        onClick={onRegenerate}
        className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-semibold bg-white text-[var(--foreground)] border border-[var(--border)] transition-all duration-200 cursor-pointer hover:border-[var(--accent)] hover:text-[var(--accent)]"
      >
        <span>🔁</span> Regenerate
      </button>
    </div>
  );
}
