"use client";

import React, { useMemo, useRef, useEffect, useState } from "react";
import type { CardComponent, FinalCardJSON } from "@/types/card";

const CARD_WIDTH = 704;
const CARD_HEIGHT = 396;

interface CardRendererProps {
  cardJson: FinalCardJSON;
}

export default function CardRenderer({ cardJson }: CardRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);

  // Responsive scaling
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const parentWidth = containerRef.current.parentElement?.clientWidth ?? CARD_WIDTH;
        const maxWidth = Math.min(parentWidth - 32, CARD_WIDTH); // 16px padding each side
        const newScale = maxWidth / CARD_WIDTH;
        setScale(Math.min(newScale, 1));
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Filter and sort visible front-side components
  const components = useMemo(() => {
    return cardJson.components
      .filter((c) => c.visible && c.cardSide === "front")
      .sort((a, b) => a.zIndex - b.zIndex);
  }, [cardJson.components]);

  return (
    <div
      ref={containerRef}
      className="flex justify-center"
      style={{ width: "100%" }}
    >
      <div
        style={{
          width: CARD_WIDTH,
          height: CARD_HEIGHT,
          transform: `scale(${scale})`,
          transformOrigin: "top center",
          marginBottom: `${CARD_HEIGHT * (scale - 1)}px`,
        }}
      >
        <div
          id="business-card"
          className="card-hero-shadow rounded-xl overflow-hidden"
          style={{
            position: "relative",
            width: CARD_WIDTH,
            height: CARD_HEIGHT,
            backgroundColor: "#ffffff",
          }}
        >
          {components.map((comp) => (
            <CardComponentView key={comp.id} component={comp} />
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── Individual component renderer ─────────────────────────────

function CardComponentView({ component }: { component: CardComponent }) {
  const { componentType, componentStyle: s, hCoords, fallbackText, zIndex } = component;

  const baseStyle: React.CSSProperties = {
    position: "absolute",
    top: hCoords.top,
    left: hCoords.left,
    width: hCoords.width,
    height: hCoords.height,
    zIndex,
    borderRadius: s.borderRadius ?? 0,
    opacity: s.opacity ?? 1,
  };

  // ─── Card background ──────────────────────────────────
  if (componentType === "cardBackground") {
    const bgStyle: React.CSSProperties = { ...baseStyle };

    if (s.backgroundType === "gradient" && s.backgroundValue) {
      bgStyle.background = s.backgroundValue;
    } else if (s.backgroundType === "image" && s.backgroundValue) {
      bgStyle.backgroundImage = `url(${s.backgroundValue})`;
      bgStyle.backgroundSize = "cover";
      bgStyle.backgroundPosition = "center";
    } else {
      bgStyle.backgroundColor = s.backgroundColor || s.backgroundValue || "#ffffff";
    }

    return <div style={bgStyle} />;
  }

  // ─── Logo ──────────────────────────────────────────────
  if (componentType === "logo") {
    const src = s.backgroundValue;
    if (!src) return null;

    const logoStyle: React.CSSProperties = {
      ...baseStyle,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxSizing: "border-box",
      overflow: "hidden",
      backgroundColor: s.backgroundColor,
      paddingTop: s.padding?.top ?? 0,
      paddingRight: s.padding?.right ?? 0,
      paddingBottom: s.padding?.bottom ?? 0,
      paddingLeft: s.padding?.left ?? 0,
    };

    return (
      <div style={logoStyle}>
        <LogoImage
          src={src}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            borderRadius: s.borderRadius ?? 0,
          }}
        />
      </div>
    );
  }

  // ─── Text / role_content ───────────────────────────────
  const textStyle: React.CSSProperties = {
    ...baseStyle,
    fontFamily: s.fontFamily || "Inter, sans-serif",
    fontWeight: s.fontWeight || "400",
    fontStyle: s.fontStyle || "normal",
    fontSize: s.fontSize ?? 14,
    color: s.color || "#000000",
    textAlign: (s.textAlign as React.CSSProperties["textAlign"]) || "left",
    letterSpacing: s.letterSpacing ?? 0,
    textTransform: (s.textTransform as React.CSSProperties["textTransform"]) || "none",
    textDecoration: s.textDecoration || "none",
    display: "flex",
    alignItems: "center",
    overflow: "hidden",
    paddingTop: s.padding?.top ?? 0,
    paddingRight: s.padding?.right ?? 0,
    paddingBottom: s.padding?.bottom ?? 0,
    paddingLeft: s.padding?.left ?? 0,
  };

  if (s.backgroundColor && s.backgroundType === "color") {
    textStyle.backgroundColor = s.backgroundColor;
  }

  const innerStyle: React.CSSProperties = {
    width: "100%",
    textAlign: textStyle.textAlign,
    display: "block",
    textDecoration: "inherit",
    color: "inherit",
  };

  if (componentType === "website" && fallbackText) {
    const url = fallbackText.startsWith("http") ? fallbackText : `https://${fallbackText}`;
    return (
      <div style={textStyle}>
        <a href={url} target="_blank" rel="noopener noreferrer" style={innerStyle}>
          {fallbackText}
        </a>
      </div>
    );
  }

  if (componentType === "email" && fallbackText) {
    return (
      <div style={textStyle}>
        <a href={`mailto:${fallbackText}`} style={innerStyle}>
          {fallbackText}
        </a>
      </div>
    );
  }

  if (componentType === "phoneNumber" && fallbackText) {
    const tel = fallbackText.replace(/[^0-9+]/g, "");
    return (
      <div style={textStyle}>
        <a href={`tel:${tel}`} style={innerStyle}>
          {fallbackText}
        </a>
      </div>
    );
  }

  return (
    <div style={textStyle}>
      <span style={innerStyle}>
        {fallbackText}
      </span>
    </div>
  );
}

// ─── Logo image with error handling ────────────────────────────

function LogoImage({ src, style }: { src: string; style: React.CSSProperties }) {
  const [hidden, setHidden] = useState(false);

  if (hidden) return null;

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt="Company logo"
      style={style}
      onError={() => setHidden(true)}
    />
  );
}
