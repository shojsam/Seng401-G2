import Phaser from "phaser";

/**
 * RoleScene — A modal overlay that shows the player's secret role.
 *
 * Launched on top of BoardGameScene (runs in parallel).
 * Toggled open/closed with the "R" key.
 *
 * Required assets in public/assets:
 *   - reformer_card.png    (Reformer role card art, transparent bg)
 *   - exploiter_card.png   (Exploiter role card art, transparent bg)
 */

const ASSETS = {
  reformer_card: "assets/reformer_card.png",
  exploiter_card: "assets/exploiter_card.png",
};

type RoleType = "reformer" | "exploiter";

interface RoleConfig {
  type: RoleType;
  label: string;
  asset: string;
  accentColor: string;
  winText: string;
  loseText: string;
  flavorText: string;
}

const ROLE_DATA: Record<RoleType, RoleConfig> = {
  reformer: {
    type: "reformer",
    label: "REFORMER",
    asset: "reformer_card",
    accentColor: "#2b9d65",
    winText:
      "You win if the board fills with sustainable policies, or if the Exploiter-in-Chief is ousted.",
    loseText:
      "You lose if the board fills with exploitative policies, or if the Exploiter-in-Chief becomes Director after 3 exploitative policies pass.",
    flavorText:
      "Stay vigilant and watch for suspicious behaviour. Root out the Exploiter-in-Chief, and remember — anyone might be lying!",
  },
  exploiter: {
    type: "exploiter",
    label: "EXPLOITER",
    asset: "exploiter_card",
    accentColor: "#c0392b",
    winText:
      "You win if the board fills with exploitative policies, or if the Exploiter-in-Chief becomes Director after 3 exploitative policies pass.",
    loseText:
      "You lose if the board fills with sustainable policies, or if the Exploiter-in-Chief is ousted.",
    flavorText:
      "Sow confusion, deflect suspicion, and push exploitative policies through. Trust no one — not even your allies!",
  },
};

export class RoleScene extends Phaser.Scene {
  private overlayEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;
  private isVisible: boolean = false;
  private currentRole: RoleType = "reformer";
  private toggleKey?: Phaser.Input.Keyboard.Key;

  constructor() {
    super({ key: "RoleScene" });
  }

  // Allow the parent to set the role before or after launch
  init(data?: { role?: RoleType }) {
    if (data?.role) {
      this.currentRole = data.role;
    }
  }

  preload() {
    this.load.image("reformer_card", ASSETS.reformer_card);
    this.load.image("exploiter_card", ASSETS.exploiter_card);
  }

  create() {
    // Hide the Phaser canvas layer for this scene — it's purely DOM
    this.cameras.main.setAlpha(0);

    // Build the DOM overlay (starts hidden)
    this.buildOverlay();

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);
  }

  // ─── PUBLIC API ───────────────────────────────────────────────────

  /** Programmatically show the overlay */
  public show() {
    if (!this.isVisible) this.toggle();
  }

  /** Programmatically hide the overlay */
  public hide() {
    if (this.isVisible) this.toggle();
  }

  public setRole(role: RoleType) {
    this.currentRole = role;
    if (this.overlayEl) {
      this.overlayEl.remove();
    }
    this.overlayEl = undefined;
    this.buildOverlay();
    const el = this.overlayEl;
    if (this.isVisible && el) {
      el.style.display = "flex";
    }
  }

  // ─── TOGGLE ───────────────────────────────────────────────────────

  private toggle() {
    this.isVisible = !this.isVisible;
    if (this.overlayEl) {
      this.overlayEl.style.display = this.isVisible ? "flex" : "none";
    }
  }

  // ─── BUILD OVERLAY ────────────────────────────────────────────────

  private buildOverlay() {
    const existing = document.getElementById("role-scene-overlay");
    if (existing) existing.remove();

    const parent =
      document.getElementById("game-container") ?? document.body;
    const role = ROLE_DATA[this.currentRole];

    // ── Scrim (full-screen dim) ─────────────────────────────────────
    const overlay = document.createElement("div");
    overlay.id = "role-scene-overlay";
    Object.assign(overlay.style, {
      position: "fixed",
      inset: "0",
      zIndex: "500",
      display: "none",
      alignItems: "center",
      justifyContent: "center",
      background: "rgba(0, 0, 0, 0.75)",
      fontFamily: '"Jersey 20", sans-serif',
      imageRendering: "pixelated",
    });

    // ── Modal card ──────────────────────────────────────────────────
    const modal = document.createElement("div");
    Object.assign(modal.style, {
      position: "relative",
      width: "90%",
      maxWidth: "680px",
      background: "#2a2e33",
      border: `4px solid ${role.accentColor}`,
      borderRadius: "4px",
      padding: "36px 34px 32px",
      boxSizing: "border-box",
      boxShadow: "6px 6px 0 #000000",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "0px",
      imageRendering: "pixelated",
    });

    // ── "YOU ARE:" heading ──────────────────────────────────────────
    const heading = document.createElement("div");
    heading.textContent = `YOU ARE: ${role.label}`;
    Object.assign(heading.style, {
      fontSize: "42px",
      fontWeight: "400",
      color: "#e8e4dc",
      textTransform: "uppercase",
      letterSpacing: "2px",
      fontFamily: '"Jersey 20", sans-serif',
      width: "100%",
      textAlign: "left",
      marginBottom: "20px",
    });
    modal.appendChild(heading);

    // ── Content row (card image + text) ─────────────────────────────
    const contentRow = document.createElement("div");
    Object.assign(contentRow.style, {
      display: "flex",
      flexDirection: "row",
      alignItems: "flex-start",
      gap: "28px",
      width: "100%",
    });

    // Card image wrapper
    const cardWrap = document.createElement("div");
    Object.assign(cardWrap.style, {
      flexShrink: "0",
      width: "200px",
      height: "280px",
      overflow: "hidden",
      background: "rgba(26, 40, 64, 0.6)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      imageRendering: "pixelated",
    });

    const cardImg = document.createElement("img");
    cardImg.src = `assets/${this.currentRole === "reformer" ? "reformer_card" : "exploiter_card"}.png`;
    cardImg.alt = role.label;
    Object.assign(cardImg.style, {
      width: "100%",
      height: "100%",
      objectFit: "cover",
      imageRendering: "pixelated",
    });
    cardWrap.appendChild(cardImg);

    // Text column
    const textCol = document.createElement("div");
    Object.assign(textCol.style, {
      display: "flex",
      flexDirection: "column",
      gap: "16px",
      flex: "1",
    });

    // Win text
    const winP = document.createElement("div");
    winP.textContent = role.winText;
    Object.assign(winP.style, {
      fontSize: "24px",
      lineHeight: "1.3",
      color: "#e8e4dc",
      fontFamily: '"Jersey 20", sans-serif',
      letterSpacing: "0.4px",
    });

    // Lose text
    const loseP = document.createElement("div");
    loseP.textContent = role.loseText;
    Object.assign(loseP.style, {
      fontSize: "24px",
      lineHeight: "1.3",
      color: "#e8e4dc",
      fontFamily: '"Jersey 20", sans-serif',
      letterSpacing: "0.4px",
    });

    // Flavor text (highlighted in accent color)
    const flavorP = document.createElement("div");
    flavorP.textContent = role.flavorText;
    Object.assign(flavorP.style, {
      fontSize: "24px",
      lineHeight: "1.3",
      color: role.accentColor,
      fontFamily: '"Jersey 20", sans-serif',
      letterSpacing: "0.4px",
      fontStyle: "normal",
    });

    textCol.appendChild(winP);
    textCol.appendChild(loseP);
    textCol.appendChild(flavorP);
    contentRow.appendChild(cardWrap);
    contentRow.appendChild(textCol);
    modal.appendChild(contentRow);

    // ── OKAY button ─────────────────────────────────────────────────
    const shadowColor = this.darkenColor(role.accentColor, 0.4);
    const btn = document.createElement("button");
    btn.textContent = "OKAY";
    Object.assign(btn.style, {
      marginTop: "28px",
      width: "200px",
      height: "64px",
      borderRadius: "4px",
      border: `4px solid #bfa76a`,
      background: role.accentColor,
      color: "#f0ebe3",
      fontSize: "34px",
      fontWeight: "400",
      textTransform: "uppercase",
      letterSpacing: "2px",
      cursor: "pointer",
      fontFamily: '"Jersey 20", sans-serif',
      boxShadow: `4px 4px 0 ${shadowColor}`,
      transition: "none",
      imageRendering: "pixelated",
    });

    btn.addEventListener("mousedown", () => {
      btn.style.transform = "translateX(4px) translateY(4px)";
      btn.style.boxShadow = `0 0 0 ${shadowColor}`;
    });
    btn.addEventListener("mouseup", () => {
      btn.style.transform = "translateX(0) translateY(0)";
      btn.style.boxShadow = `4px 4px 0 ${shadowColor}`;
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "translateX(0) translateY(0)";
      btn.style.boxShadow = `4px 4px 0 ${shadowColor}`;
    });

    btn.addEventListener("click", () => {
    this.events.emit("role-acknowledged");
    this.toggle();
  });

    modal.appendChild(btn);

    overlay.appendChild(modal);
    parent.appendChild(overlay);
    this.overlayEl = overlay;

    // ── Inject styles ───────────────────────────────────────────────
    const oldStyle = document.getElementById("role-scene-style");
    if (oldStyle) oldStyle.remove();

    const style = document.createElement("style");
    style.id = "role-scene-style";
    style.textContent = `
      #role-scene-overlay * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }
      #role-scene-overlay button:hover {
        filter: brightness(1.12);
      }
      @media (max-width: 600px) {
        #role-scene-overlay > div {
          padding: 24px 18px 22px !important;
        }
        #role-scene-overlay > div > div:nth-child(2) {
          flex-direction: column !important;
          align-items: center !important;
        }
        #role-scene-overlay > div > div:nth-child(2) > div:first-child {
          width: 160px !important;
          height: 224px !important;
        }
      }
    `;
    document.head.appendChild(style);
    this.injectedStyleEl = style;
  }

  // ─── HELPERS ──────────────────────────────────────────────────────

  private darkenColor(hex: string, amount: number): string {
    const num = parseInt(hex.replace("#", ""), 16);
    const r = Math.max(0, Math.floor(((num >> 16) & 0xff) * (1 - amount)));
    const g = Math.max(0, Math.floor(((num >> 8) & 0xff) * (1 - amount)));
    const b = Math.max(0, Math.floor((num & 0xff) * (1 - amount)));
    return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
  }

  // ─── CLEANUP ──────────────────────────────────────────────────────

  private cleanup() {
    if (this.overlayEl) {
      this.overlayEl.remove();
      this.overlayEl = undefined;
    }
    if (this.injectedStyleEl) {
      this.injectedStyleEl.remove();
      this.injectedStyleEl = undefined;
    }
  }
}