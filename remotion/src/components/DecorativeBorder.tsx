import React from "react";
import { AbsoluteFill } from "remotion";
import type { BrandTokens } from "../types";
import { roles } from "../design";

/**
 * A thin editorial double-line frame with small corner ticks — the ornate
 * border energy of the reference, kept clean so it frames without fighting the
 * art. Ink lines, inset from the edges. Static overlay.
 */
export const DecorativeBorder: React.FC<{ tokens: BrandTokens; inset?: number }> = ({
  tokens,
  inset = 28,
}) => {
  const { ink } = roles(tokens);
  const corner = (style: React.CSSProperties) => (
    <div
      style={{
        position: "absolute",
        width: 26,
        height: 26,
        borderColor: ink,
        ...style,
      }}
    />
  );

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* outer thin + inner thicker line */}
      <div style={{ position: "absolute", inset, border: `2px solid ${ink}`, opacity: 0.85 }} />
      <div style={{ position: "absolute", inset: inset + 8, border: `5px solid ${ink}`, opacity: 0.9 }} />
      {/* corner ticks on the inner frame */}
      {corner({ top: inset + 8, left: inset + 8, borderTop: `5px solid ${ink}`, borderLeft: `5px solid ${ink}` })}
      {corner({ top: inset + 8, right: inset + 8, borderTop: `5px solid ${ink}`, borderRight: `5px solid ${ink}` })}
      {corner({ bottom: inset + 8, left: inset + 8, borderBottom: `5px solid ${ink}`, borderLeft: `5px solid ${ink}` })}
      {corner({ bottom: inset + 8, right: inset + 8, borderBottom: `5px solid ${ink}`, borderRight: `5px solid ${ink}` })}
    </AbsoluteFill>
  );
};
