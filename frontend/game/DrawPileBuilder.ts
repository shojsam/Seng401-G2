/**
 * game/DrawPileBuilder.ts — Builds the card draw pile display.
 */
import { TOTAL_HUD } from "./HUDBuilder";

const BASE_WIDTH = 1920;
const ASSET_POLICY_FOLDER = "assets/policy_folder1.png";

export function createDrawPile(
  policyDrawCount: number,
  getBgAspect: () => number,
  createScaledWrapper: (id: string, zIndex: string) => { wrapper: HTMLDivElement; inner: HTMLDivElement },
): HTMLDivElement {
  const existing = document.getElementById("draw-pile-wrapper");
  if (existing) existing.remove();

  const parent = document.getElementById("game-container") ?? document.body;
  const baseBgH = BASE_WIDTH * getBgAspect();

  const holderW = BASE_WIDTH * 0.42;
  const holderH = holderW * 0.65;
  const holderY = TOTAL_HUD + baseBgH * 0.35 - holderH / 2;

  const pileTop = holderY + holderH + 70;
  const pileCenterX = BASE_WIDTH * 0.25;
  const pileW = Math.floor(56 * 2.25) + 60;

  const { wrapper, inner } = createScaledWrapper("draw-pile-wrapper", "10");

  const pile = buildDrawPile(policyDrawCount);
  pile.id = "draw-pile";
  Object.assign(pile.style, {
    position: "absolute",
    top: `${pileTop}px`,
    left: `${pileCenterX - pileW / 2}px`,
    pointerEvents: "none",
  });

  inner.appendChild(pile);
  parent.appendChild(wrapper);
  return wrapper;
}

function buildDrawPile(count: number): HTMLDivElement {
  const scale = 2.25;
  const cardW = Math.floor(56 * scale);
  const cardH = Math.floor(74 * scale);
  const stackOffset = 4.5;
  const maxVisibleCards = Math.min(count, 16);

  const wrapper = document.createElement("div");
  Object.assign(wrapper.style, {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    fontFamily: '"Jersey 20", sans-serif',
  });

  const tableW = cardW + 60;
  const labelH = 46;
  const labelGap = 12;
  const topPad = 16;
  const bottomPad = 14;
  const tableH = topPad + cardH + labelGap + labelH + bottomPad;

  const table = document.createElement("div");
  Object.assign(table.style, {
    width: `${tableW}px`,
    height: `${tableH}px`,
    background: "linear-gradient(to bottom, #5c3d2e, #4a3122)",
    border: "4px solid #d4a843",
    boxShadow: "4px 4px 0 rgba(0,0,0,0.5)",
    boxSizing: "border-box",
    position: "relative",
  });

  const stackContainer = document.createElement("div");
  Object.assign(stackContainer.style, {
    position: "absolute",
    left: "50%",
    transform: "translateX(-50%)",
    bottom: `${bottomPad + labelH + labelGap}px`,
    width: `${cardW}px`,
    height: `${cardH + maxVisibleCards * stackOffset}px`,
  });

  for (let i = 0; i < maxVisibleCards; i++) {
    const card = document.createElement("div");
    const offsetY = i * stackOffset;
    Object.assign(card.style, {
      position: "absolute",
      bottom: `${offsetY}px`,
      left: "50%",
      transform: "translateX(-50%)",
      width: `${cardW}px`,
      height: `${cardH}px`,
      backgroundImage: `url("${ASSET_POLICY_FOLDER}")`,
      backgroundSize: "cover",
      backgroundPosition: "center",
      backgroundRepeat: "no-repeat",
      imageRendering: "pixelated",
      borderRadius: "4px",
      boxSizing: "border-box",
    });
    stackContainer.appendChild(card);
  }
  table.appendChild(stackContainer);

  const label = document.createElement("div");
  label.textContent = `${count}`;
  Object.assign(label.style, {
    position: "absolute",
    bottom: `${bottomPad}px`,
    left: "50%",
    transform: "translateX(-50%)",
    fontSize: "32px",
    color: "#f0ebe3",
    textAlign: "center",
    letterSpacing: "1px",
    background: "#3a2518",
    borderRadius: "4px",
    padding: "2px 16px",
    minWidth: "40px",
    height: `${labelH}px`,
    lineHeight: `${labelH}px`,
    boxSizing: "border-box",
  });
  table.appendChild(label);

  wrapper.appendChild(table);
  return wrapper;
}