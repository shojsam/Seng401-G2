/**
 * game/PhaseAnnouncer.ts — Full-screen phase transition overlay.
 *
 * Dims the entire screen and displays the phase title + subtitle,
 * fading in over 0.4s, holding for ~2.2s, then fading out over 0.4s.
 * Total duration ≈ 3 seconds.
 */

import type { GameState } from "./GameState";

const OVERLAY_ID = "phase-announcer-overlay";
const FADE_IN_MS = 400;
const HOLD_MS = 2200;
const FADE_OUT_MS = 400;

interface PhaseInfo {
  title: string;
  subtitle: string;
}

/**
 * Map a gamePhase string to the announcement title + subtitle.
 * Returns null for phases that shouldn't show an announcement
 * (lobby, role_reveal which has its own overlay, etc.).
 */
function getPhaseInfo(phase: string, state: GameState): PhaseInfo | null {
  switch (phase) {
    case "nomination":
      return {
        title: "NOMINATION",
        subtitle: state.username === state.currentLeader
          ? "You are the Leader — nominate a Vice."
          : `${state.currentLeader || "The Leader"} is choosing a Vice.`,
      };
    case "election":
      return {
        title: "VOTING",
        subtitle: `Vote to approve or reject ${state.currentLeader || "Leader"} & ${state.currentVice || "Vice"}.`,
      };
    case "voting_results":
      return null; // Handled by HUD vote badges + phase bar tally
    case "leader_discard":
      return {
        title: "POLICY REVIEW",
        subtitle: state.username === state.currentLeader
          ? "You drew 3 policies — discard one."
          : `${state.currentLeader || "The Leader"} is reviewing policies.`,
      };
    case "vice_enact":
      return {
        title: "ENACT POLICY",
        subtitle: state.username === state.currentVice
          ? "Choose a policy to enact."
          : `${state.currentVice || "The Vice"} is choosing a policy.`,
      };
    case "resolution":
      return {
        title: "POLICY ENACTED",
        subtitle: "A new policy has been put into effect.",
      };
    case "game_over":
      return {
        title: "GAME OVER",
        subtitle: "",
      };
    default:
      return null;
  }
}

/** Inject the CSS keyframe styles once. */
let stylesInjected = false;
function injectStyles() {
  if (stylesInjected) return;
  stylesInjected = true;

  const style = document.createElement("style");
  style.id = "phase-announcer-styles";
  style.textContent = `
    @keyframes phase-announcer-fade-in {
      from { opacity: 0; }
      to   { opacity: 1; }
    }
    @keyframes phase-announcer-fade-out {
      from { opacity: 1; }
      to   { opacity: 0; }
    }
    @keyframes phase-announcer-title-slide {
      from {
        opacity: 0;
        transform: translateY(18px) scale(0.92);
      }
      to {
        opacity: 1;
        transform: translateY(0) scale(1);
      }
    }
    @keyframes phase-announcer-subtitle-slide {
      from {
        opacity: 0;
        transform: translateY(12px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  `;
  document.head.appendChild(style);
}

/** Remove any existing announcer overlay. */
function removeExisting() {
  const existing = document.getElementById(OVERLAY_ID);
  if (existing) existing.remove();
}

/**
 * Show the phase announcement overlay.
 * Call this from onPhaseChange in GameSocketHandler.
 * Returns the total duration in ms (0 if no announcement was shown).
 * Pass `subtitleOverride` to replace the default subtitle text.
 */
export function announcePhase(phase: string, state: GameState, subtitleOverride?: string): number {
  const info = getPhaseInfo(phase, state);
  if (!info) return 0;

  if (subtitleOverride !== undefined) {
    info.subtitle = subtitleOverride;
  }

  injectStyles();
  removeExisting();

  const parent = document.getElementById("game-container") ?? document.body;

  // ── Full-screen overlay ───────────────────────────────────────
  const overlay = document.createElement("div");
  overlay.id = OVERLAY_ID;
  Object.assign(overlay.style, {
    position: "fixed",
    inset: "0",
    zIndex: "600", // Above scene overlays (500) so nothing shows during announcement
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    background: "rgba(0, 0, 0, 0.72)",
    pointerEvents: "none",
    fontFamily: '"Jersey 20", sans-serif',
    imageRendering: "pixelated",
    animation: `phase-announcer-fade-in ${FADE_IN_MS}ms ease-out forwards`,
  });

  // ── Title ─────────────────────────────────────────────────────
  const title = document.createElement("div");
  title.textContent = info.title;
  Object.assign(title.style, {
    fontSize: "clamp(48px, 8vw, 96px)",
    fontWeight: "400",
    color: "#d4a843",
    letterSpacing: "6px",
    textTransform: "uppercase",
    textAlign: "center",
    textShadow: "0 4px 16px rgba(0,0,0,0.6), 0 0 40px rgba(212,168,67,0.25)",
    animation: `phase-announcer-title-slide ${FADE_IN_MS}ms ease-out forwards`,
    marginBottom: "16px",
  });
  overlay.appendChild(title);

  // ── Subtitle ──────────────────────────────────────────────────
  if (info.subtitle) {
    const subtitle = document.createElement("div");
    subtitle.textContent = info.subtitle;
    Object.assign(subtitle.style, {
      fontSize: "clamp(20px, 3vw, 36px)",
      fontWeight: "400",
      color: "#e8e4dc",
      letterSpacing: "2px",
      textAlign: "center",
      textShadow: "0 2px 8px rgba(0,0,0,0.5)",
      opacity: "0",
      animation: `phase-announcer-subtitle-slide ${FADE_IN_MS}ms ease-out ${150}ms forwards`,
      maxWidth: "80%",
    });
    overlay.appendChild(subtitle);
  }

  // ── Decorative line ───────────────────────────────────────────
  const line = document.createElement("div");
  Object.assign(line.style, {
    width: "120px",
    height: "3px",
    background: "linear-gradient(90deg, transparent, #d4a843, transparent)",
    marginTop: "24px",
    opacity: "0",
    animation: `phase-announcer-subtitle-slide ${FADE_IN_MS}ms ease-out ${250}ms forwards`,
  });
  overlay.appendChild(line);

  parent.appendChild(overlay);

  // ── Fade out after hold period ────────────────────────────────
  const totalDuration = FADE_IN_MS + HOLD_MS + FADE_OUT_MS;
  setTimeout(() => {
    overlay.style.animation = `phase-announcer-fade-out ${FADE_OUT_MS}ms ease-in forwards`;
    setTimeout(() => {
      overlay.remove();
    }, FADE_OUT_MS);
  }, FADE_IN_MS + HOLD_MS);

  return totalDuration;
}

/**
 * Immediately dismiss any active phase announcer (e.g. on game reset).
 */
export function dismissAnnouncer() {
  removeExisting();
}