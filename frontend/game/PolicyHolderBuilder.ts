/**
 * game/PolicyHolderBuilder.ts — Builds the sustainable / exploitative policy holder panels.
 *
 * Filled slots show the policy_folder1.png image and are clickable
 * to open PolicyDescScene with the policy's title and description.
 */
import type { GameState, EnactedPolicy } from "./GameState";
import { TOTAL_HUD } from "./HudBuilder";

const BASE_WIDTH = 1920;
const ASSET_POLICY_FOLDER = "assets/policy_folder1.png";

/**
 * onSlotClick is called when a player clicks a filled policy slot.
 * The caller (BoardGameScene) provides a function that opens PolicyDescScene.
 */
export type SlotClickHandler = (policy: EnactedPolicy) => void;

export function createPolicyHolders(
  state: GameState,
  getBgAspect: () => number,
  createScaledWrapper: (id: string, zIndex: string) => { wrapper: HTMLDivElement; inner: HTMLDivElement },
  onSlotClick?: SlotClickHandler,
): HTMLDivElement {
  const existing = document.getElementById("policy-holders-wrapper");
  if (existing) existing.remove();

  const parent = document.getElementById("game-container") ?? document.body;
  const baseBgH = BASE_WIDTH * getBgAspect();

  const holderW = BASE_WIDTH * 0.42;
  const holderH = holderW * 0.65;
  const holderY = TOTAL_HUD + baseBgH * 0.3 - holderH / 2;

  const { wrapper, inner } = createScaledWrapper("policy-holders-wrapper", "10");
  // Allow pointer events to pass through to clickable policy slots
  wrapper.style.pointerEvents = "auto";

  const container = document.createElement("div");
  container.id = "policy-holders";
  Object.assign(container.style, {
    width: `${BASE_WIDTH}px`,
    display: "flex",
    justifyContent: "center",
    gap: `${BASE_WIDTH * 0.06}px`,
    paddingTop: `${holderY}px`,
    fontFamily: '"Jersey 20", sans-serif',
  });

  container.appendChild(
    buildHolder(
      holderW, holderH, "#66785a", "#809671",
      "SUSTAINABLE",
      "REFORMERS MUST PASS 5\nSUSTAINABLE POLICIES TO WIN",
      state.enactedSustainable, 5, onSlotClick,
    )
  );

  container.appendChild(
    buildHolder(
      holderW, holderH, "#842929", "#bc6262",
      "EXPLOITATIVE",
      "EXPLOITERS MUST PASS 3\nEXPLOITATIVE POLICIES TO WIN",
      state.enactedExploitative, 3, onSlotClick,
    )
  );

  inner.appendChild(container);
  parent.appendChild(wrapper);
  return wrapper;
}

function buildHolder(
  w: number, h: number,
  bgColor: string, borderColor: string,
  titleText: string, descText: string,
  enactedPolicies: EnactedPolicy[], total: number,
  onSlotClick?: SlotClickHandler,
): HTMLDivElement {
  const holder = document.createElement("div");
  Object.assign(holder.style, {
    width: `${w}px`,
    height: `${h}px`,
    background: bgColor,
    border: `4px solid ${borderColor}`,
    borderRadius: "4px",
    boxShadow: "4px 4px 0 rgba(0,0,0,0.5)",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "space-between",
    boxSizing: "border-box",
    padding: "16px",
    pointerEvents: "none",
  });

  const title = document.createElement("div");
  title.textContent = titleText;
  Object.assign(title.style, {
    fontSize: `${Math.max(32, Math.floor(w * 0.08))}px`,
    color: "#f0ebe3",
    letterSpacing: "3px",
    textAlign: "center",
  });
  holder.appendChild(title);

  const slotsRow = document.createElement("div");
  Object.assign(slotsRow.style, {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
  });

  const scale = 2.25;
  const slotW = Math.floor(56 * scale);
  const slotH = Math.floor(74 * scale);
  const filled = enactedPolicies.length;

  for (let i = 0; i < total; i++) {
    const slot = document.createElement("div");
    const isFilled = i < filled;

    Object.assign(slot.style, {
      width: `${slotW}px`,
      height: `${slotH}px`,
      border: `4px solid ${borderColor}`,
      boxSizing: "border-box",
      position: "relative",
      overflow: "hidden",
    });

    if (isFilled) {
      // Show policy folder image
      Object.assign(slot.style, {
        backgroundImage: `url("${ASSET_POLICY_FOLDER}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        imageRendering: "pixelated",
        cursor: "pointer",
        pointerEvents: "auto",
      });

      // Hover effect
      slot.addEventListener("mouseenter", () => {
        slot.style.outline = "3px solid #d4a843";
        slot.style.outlineOffset = "-3px";
        slot.style.filter = "brightness(1.15)";
      });
      slot.addEventListener("mouseleave", () => {
        slot.style.outline = "none";
        slot.style.filter = "none";
      });

      // Click → open PolicyDescScene
      const policy = enactedPolicies[i];
      slot.addEventListener("click", () => {
        if (onSlotClick) onSlotClick(policy);
      });
    } else {
      // Empty slot
      Object.assign(slot.style, {
        background: "rgba(0, 0, 0, 0.25)",
        pointerEvents: "none",
      });
    }

    slotsRow.appendChild(slot);
  }
  holder.appendChild(slotsRow);

  const desc = document.createElement("div");
  desc.textContent = descText;
  Object.assign(desc.style, {
    fontSize: `${Math.max(18, Math.floor(w * 0.045))}px`,
    color: "#d4cfc5",
    textAlign: "center",
    lineHeight: "1.3",
    whiteSpace: "pre-line",
  });
  holder.appendChild(desc);

  return holder;
}