/**
 * game/ElectionTrackerBuilder.ts — Builds the failed election tracker visual.
 *
 * A wooden table with 4 slots. A marker sits on the slot matching
 * the current election_tracker value (0 = first slot, 3 = fourth slot).
 * When the tracker reaches 3, the top policy is force-enacted and it resets.
 * Positioned bottom-right of the board, below the exploitative holder.
 */
import type { GameState } from "./GameState";
import { TOTAL_HUD } from "./HUDBuilder";

const BASE_WIDTH = 1920;

export function createElectionTracker(
  state: GameState,
  getBgAspect: () => number,
  createScaledWrapper: (id: string, zIndex: string) => { wrapper: HTMLDivElement; inner: HTMLDivElement },
): HTMLDivElement {
  const existing = document.getElementById("election-tracker-wrapper");
  if (existing) existing.remove();

  const parent = document.getElementById("game-container") ?? document.body;
  const baseBgH = BASE_WIDTH * getBgAspect();

  // Position: below exploitative holder, right side of board
  const holderW = BASE_WIDTH * 0.42;
  const holderH = holderW * 0.65;
  const holderY = TOTAL_HUD + baseBgH * 0.35 - holderH / 2;
  const trackerTop = holderY + holderH + 70;
  const trackerCenterX = BASE_WIDTH * 0.75;

  const { wrapper, inner } = createScaledWrapper("election-tracker-wrapper", "15");
  wrapper.style.overflow = "visible";

  const tracker = buildTracker(state.electionTracker);
  tracker.id = "election-tracker";
  Object.assign(tracker.style, {
    position: "absolute",
    top: `${trackerTop}px`,
    left: `${trackerCenterX - 180}px`,
    pointerEvents: "none",
  });

  inner.appendChild(tracker);
  parent.appendChild(wrapper);
  return wrapper;
}

function buildTracker(trackerValue: number): HTMLDivElement {
  const slotCount = 4;
  const slotSize = 74;
  const slotGap = 18;
  const markerSize = 52;
  const padding = 28;

  const tableW = padding * 2 + slotCount * slotSize + (slotCount - 1) * slotGap;
  const tableH = 190;

  const container = document.createElement("div");
  Object.assign(container.style, {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    fontFamily: '"Jersey 20", sans-serif',
  });

  // ── Table background ──────────────────────────────────────────
  const table = document.createElement("div");
  Object.assign(table.style, {
    width: `${tableW}px`,
    height: `${tableH}px`,
    background: "linear-gradient(to bottom, #5c3d2e, #4a3122)",
    border: "4px solid #d4a843",
    boxShadow: "4px 4px 0 rgba(0,0,0,0.5)",
    boxSizing: "border-box",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    padding: "14px",
    position: "relative",
  });

  // ── Title ─────────────────────────────────────────────────────
  const title = document.createElement("div");
  title.textContent = "ELECTION TRACKER";
  Object.assign(title.style, {
    fontSize: "26px",
    color: "#d4a843",
    letterSpacing: "3px",
    textAlign: "center",
  });
  table.appendChild(title);

  // ── Slots row ─────────────────────────────────────────────────
  const slotsRow = document.createElement("div");
  Object.assign(slotsRow.style, {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: `${slotGap}px`,
  });

  for (let i = 0; i < slotCount; i++) {
    const slot = document.createElement("div");
    const isActive = i === trackerValue;
    const isPast = i < trackerValue;
    const isDanger = i === slotCount - 1; // Last slot = danger zone

    Object.assign(slot.style, {
      width: `${slotSize}px`,
      height: `${slotSize}px`,
      border: `4px solid ${isDanger ? "#bc6262" : "#8a7a5e"}`,
      background: isDanger
        ? "rgba(132, 41, 41, 0.4)"
        : "rgba(0, 0, 0, 0.25)",
      boxSizing: "border-box",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      position: "relative",
    });

    // Square marker on the active slot
    if (isActive) {
      const marker = document.createElement("div");
      Object.assign(marker.style, {
        width: `${markerSize}px`,
        height: `${markerSize}px`,
        background: isDanger ? "#c94040" : "#d4a843",
        border: `3px solid ${isDanger ? "#ff6b6b" : "#bfa76a"}`,
      });
      slot.appendChild(marker);
    }

    // Small square for past positions
    if (isPast && !isActive) {
      const dot = document.createElement("div");
      Object.assign(dot.style, {
        width: "14px",
        height: "14px",
        background: "rgba(212, 168, 67, 0.35)",
      });
      slot.appendChild(dot);
    }

    slotsRow.appendChild(slot);
  }

  table.appendChild(slotsRow);

  // ── Labels row ────────────────────────────────────────────────
  const labelsRow = document.createElement("div");
  Object.assign(labelsRow.style, {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: `${slotGap}px`,
  });

  const labels = ["0", "1", "2", "3!"];
  for (let i = 0; i < slotCount; i++) {
    const label = document.createElement("div");
    label.textContent = labels[i];
    Object.assign(label.style, {
      width: `${slotSize}px`,
      textAlign: "center",
      fontSize: "20px",
      color: i === slotCount - 1 ? "#bc6262" : "#8a7a5e",
      letterSpacing: "1px",
    });
    labelsRow.appendChild(label);
  }

  table.appendChild(labelsRow);

  container.appendChild(table);
  return container;
}