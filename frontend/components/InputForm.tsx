"use client";

import React, { useState } from "react";
import type { UserData } from "@/types/card";

interface InputFormProps {
  onSubmit: (url: string, userData: UserData) => void;
}

export default function InputForm({ onSubmit }: InputFormProps) {
  const [url, setUrl] = useState("");
  const [fullName, setFullName] = useState("");
  const [position, setPosition] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");

  const isValid =
    url.trim() !== "" &&
    fullName.trim() !== "" &&
    position.trim() !== "" &&
    email.trim() !== "";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) return;
    onSubmit(url.trim(), {
      fullName: fullName.trim(),
      position: position.trim(),
      email: email.trim(),
      phoneNumber: phoneNumber.trim(),
    });
  };

  return (
    <div className="animate-fade-in flex flex-col items-center justify-center px-4 py-16">
      {/* Header */}
      <div className="text-center mb-10 max-w-lg">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--accent-light)] text-[var(--accent)] text-xs font-semibold tracking-wide uppercase mb-5">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
          </svg>
          AI-Powered
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-[var(--foreground)] mb-3">
          Rolo AI Card Generator
        </h1>
        <p className="text-[var(--muted)] text-base leading-relaxed">
          Enter a company website and your details — our AI will analyze the
          brand and generate a professional business card in seconds.
        </p>
      </div>

      {/* Form card */}
      <form
        onSubmit={handleSubmit}
        id="generate-form"
        className="w-full max-w-md bg-[var(--card-bg)] rounded-2xl border border-[var(--border)] p-7 space-y-5"
        style={{ boxShadow: "0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.04)" }}
      >
        {/* URL */}
        <div>
          <label htmlFor="url-input" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
            Company Website
          </label>
          <div className="relative">
            <span className="absolute inset-y-0 left-3 flex items-center text-[var(--muted)]">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 0 0 8.716-6.747M12 21a9.004 9.004 0 0 1-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 0 1 7.843 4.582M12 3a8.997 8.997 0 0 0-7.843 4.582m15.686 0A11.953 11.953 0 0 1 12 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0 1 21 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0 1 12 16.5a17.92 17.92 0 0 1-8.716-2.247m0 0A9 9 0 0 1 3 12c0-1.605.42-3.113 1.157-4.418" />
              </svg>
            </span>
            <input
              id="url-input"
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition placeholder:text-[#9ca3af]"
            />
          </div>
        </div>

        {/* Two-col */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="fullname-input" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
              Full Name
            </label>
            <input
              id="fullname-input"
              type="text"
              placeholder="Jane Smith"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition placeholder:text-[#9ca3af]"
            />
          </div>
          <div>
            <label htmlFor="position-input" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
              Position
            </label>
            <input
              id="position-input"
              type="text"
              placeholder="Product Designer"
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition placeholder:text-[#9ca3af]"
            />
          </div>
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email-input" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
            Email
          </label>
          <input
            id="email-input"
            type="email"
            placeholder="jane@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition placeholder:text-[#9ca3af]"
          />
        </div>

        {/* Phone */}
        <div>
          <label htmlFor="phone-input" className="block text-sm font-medium text-[var(--foreground)] mb-1.5">
            Phone Number
          </label>
          <input
            id="phone-input"
            type="tel"
            placeholder="+1 (555) 123-4567"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl border border-[var(--border)] bg-[var(--background)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition placeholder:text-[#9ca3af]"
          />
        </div>

        {/* Submit */}
        <button
          id="generate-button"
          type="submit"
          disabled={!isValid}
          className="w-full py-3 rounded-xl text-sm font-semibold text-white transition-all duration-200
                     disabled:opacity-40 disabled:cursor-not-allowed
                     cursor-pointer"
          style={{
            background: isValid
              ? "linear-gradient(135deg, #6366f1, #8b5cf6)"
              : "#a5b4fc",
          }}
          onMouseEnter={(e) => {
            if (isValid)
              (e.currentTarget.style.background =
                "linear-gradient(135deg, #4f46e5, #7c3aed)");
          }}
          onMouseLeave={(e) => {
            if (isValid)
              (e.currentTarget.style.background =
                "linear-gradient(135deg, #6366f1, #8b5cf6)");
          }}
        >
          <span className="inline-flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456Z" />
            </svg>
            Generate Card
          </span>
        </button>
      </form>

      {/* Footer */}
      <p className="mt-6 text-xs text-[var(--muted)]">
        Powered by AI · Typically takes 15-30 seconds
      </p>
    </div>
  );
}
