"use client";

import React from "react";
import { ReviewStatus, ReviewVerdict } from "@/lib/types";

export type GlyphType =
  | "ready"
  | "approved"
  | "building"
  | "processing"
  | "queued"
  | "pending"
  | "canceled"
  | "failed"
  | "changes_requested"
  | "comment";

interface InkGlyphProps {
  status?: ReviewStatus | string;
  verdict?: ReviewVerdict | string;
  type?: GlyphType;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function InkGlyph({
  status,
  verdict,
  type,
  size = "md",
  className = "",
}: InkGlyphProps) {
  let resolvedType: GlyphType = "queued";

  if (type) {
    resolvedType = type;
  } else if (status === "FAILED" || verdict === "REQUEST_CHANGES") {
    resolvedType = "failed";
  } else if (status === "PROCESSING") {
    resolvedType = "processing";
  } else if (status === "PENDING") {
    resolvedType = "queued";
  } else if (verdict === "APPROVE") {
    resolvedType = "approved";
  } else if (verdict === "COMMENT") {
    resolvedType = "comment";
  } else if (status === "COMPLETED") {
    resolvedType = "ready";
  }

  const dim = size === "sm" ? 12 : size === "lg" ? 18 : 14;

  switch (resolvedType) {
    case "ready":
    case "approved":
      // Solid filled circle
      return (
        <svg
          width={dim}
          height={dim}
          viewBox="0 0 16 16"
          className={`inline-block flex-shrink-0 text-[var(--ink-primary)] ${className}`}
          fill="currentColor"
          aria-label="Approved / Ready"
        >
          <circle cx="8" cy="8" r="6" />
        </svg>
      );

    case "building":
    case "processing":
      // Half-filled ring (building/running)
      return (
        <svg
          width={dim}
          height={dim}
          viewBox="0 0 16 16"
          className={`inline-block flex-shrink-0 text-[var(--ink-primary)] animate-spin [animation-duration:2.5s] ${className}`}
          aria-label="Processing / In-Flight"
        >
          <circle
            cx="8"
            cy="8"
            r="6"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.75"
          />
          <path
            d="M 8 2 A 6 6 0 0 1 8 14 Z"
            fill="currentColor"
          />
        </svg>
      );

    case "queued":
    case "pending":
      // Empty ring
      return (
        <svg
          width={dim}
          height={dim}
          viewBox="0 0 16 16"
          className={`inline-block flex-shrink-0 text-[var(--ink-muted)] ${className}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-label="Queued / Pending"
        >
          <circle cx="8" cy="8" r="6" />
        </svg>
      );

    case "canceled":
      // Dashed ring
      return (
        <svg
          width={dim}
          height={dim}
          viewBox="0 0 16 16"
          className={`inline-block flex-shrink-0 text-[var(--ink-muted)] ${className}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          strokeDasharray="2 2"
          aria-label="Canceled"
        >
          <circle cx="8" cy="8" r="6" />
        </svg>
      );

    case "failed":
    case "changes_requested":
      // Signal Red circle-x
      return (
        <svg
          width={dim}
          height={dim}
          viewBox="0 0 16 16"
          className={`inline-block flex-shrink-0 text-[var(--signal-red)] ${className}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-label="Failed / Changes Requested"
        >
          <circle cx="8" cy="8" r="6.25" />
          <line x1="5.25" y1="5.25" x2="10.75" y2="10.75" strokeLinecap="round" />
          <line x1="10.75" y1="5.25" x2="5.25" y2="10.75" strokeLinecap="round" />
        </svg>
      );

    case "comment":
    default:
      // Neutral circle with dot
      return (
        <svg
          width={dim}
          height={dim}
          viewBox="0 0 16 16"
          className={`inline-block flex-shrink-0 text-[var(--ink-secondary)] ${className}`}
          fill="none"
          stroke="currentColor"
          strokeWidth="1.75"
          aria-label="Comment"
        >
          <circle cx="8" cy="8" r="6" />
          <circle cx="8" cy="8" r="2" fill="currentColor" />
        </svg>
      );
  }
}
