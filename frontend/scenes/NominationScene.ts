import Phaser from "phaser";

const ASSETS = {
  player_basecard: "assets/player_basecard.png",
};

interface CandidateData {
  name: string;
  eligible: boolean;
  characterId?: number;
  roleLabel?: string;
  roleColor?: string;
}

interface NominationData {
  players?: CandidateData[];
}

export class NominationScene extends Phaser.Scene {
  private overlayEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;
  private visible: boolean = false;
  private keyHandler?: (e: KeyboardEvent) => void;

  private candidates: CandidateData[] = [];
  private selectedIndex: number | null = null;

  constructor() {
    super({ key: "NominationScene" });
  }

  init(data: NominationData) {
    if (data.players) this.candidates = data.players;
  }

  create() {
    this.cameras.main.setVisible(false);

    this.buildOverlay();

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);
  }

  // ─── TOGGLE ───────────────────────────────────────────────────────

  private toggleOverlay() {
    this.visible = !this.visible;
    if (this.overlayEl) {
      this.overlayEl.style.display = this.visible ? "flex" : "none";
    }
  }

  public show(data?: NominationData) {
    if (data?.players) this.candidates = data.players;
    this.selectedIndex = null;
    this.buildOverlay();
    this.visible = true;
    if (this.overlayEl) this.overlayEl.style.display = "flex";
  }

  public hide() {
    this.visible = false;
    if (this.overlayEl) this.overlayEl.style.display = "none";
  }

  // ─── BUILD DOM ────────────────────────────────────────────────────

  private buildOverlay() {
    const existing = document.getElementById("nomination-overlay");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    // ── Full-screen backdrop ────────────────────────────────────────
    const overlay = document.createElement("div");
    overlay.id = "nomination-overlay";
    Object.assign(overlay.style, {
      position: "fixed",
      inset: "0",
      display: "none",
      alignItems: "center",
      justifyContent: "center",
      zIndex: "500",
      background: "rgba(0, 0, 0, 0.75)",
      fontFamily: '"Jersey 20", sans-serif',
      imageRendering: "pixelated",
    });

    // ── Panel ───────────────────────────────────────────────────────
    const panel = document.createElement("div");
    Object.assign(panel.style, {
      background: "#2a2e33",
      border: "4px solid #4a4e55",
      padding: "36px 44px 40px",
      maxWidth: "750px",
      width: "90%",
      boxSizing: "border-box",
      display: "flex",
      flexDirection: "column",
      alignItems: "flex-start",
      gap: "0px",
      boxShadow: "6px 6px 0 #000000",
      imageRendering: "pixelated",
    });

    // ── Title ───────────────────────────────────────────────────────
    const title = document.createElement("div");
    title.textContent = "NOMINATION";
    Object.assign(title.style, {
      fontSize: "42px",
      fontWeight: "400",
      color: "#e8e4dc",
      letterSpacing: "2px",
      marginBottom: "12px",
      fontFamily: '"Jersey 20", sans-serif',
    });
    panel.appendChild(title);

    // ── Description ─────────────────────────────────────────────────
    const desc = document.createElement("div");
    desc.textContent = "Nominate a player to become the next Vice.";
    Object.assign(desc.style, {
      fontSize: "24px",
      color: "#9e9a92",
      fontFamily: '"Jersey 20", sans-serif',
      lineHeight: "1.3",
      marginBottom: "24px",
    });
    panel.appendChild(desc);

    // ── Player cards row ────────────────────────────────────────────
    const cardRow = document.createElement("div");
    Object.assign(cardRow.style, {
      display: "flex",
      gap: "18px",
      width: "100%",
      justifyContent: "center",
      flexWrap: "wrap",
      marginBottom: "28px",
    });

    const cardEls: HTMLDivElement[] = [];

    this.candidates.forEach((candidate, idx) => {
      const isEligible = candidate.eligible;

      const card = document.createElement("div");
      card.classList.add("nom-card");
      card.dataset.index = String(idx);

      Object.assign(card.style, {
        width: "130px",
        height: "210px",
        backgroundImage: `url("${ASSETS.player_basecard}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-end",
        paddingBottom: "10px",
        boxSizing: "border-box",
        overflow: "hidden",
        imageRendering: "pixelated",
        cursor: isEligible ? "pointer" : "default",
        opacity: isEligible ? "1" : "0.5",
        filter: isEligible ? "none" : "grayscale(0.6) brightness(0.6)",
        position: "relative",
      });

      // Restricted overlay text (previously "TERM LIMITED")
      if (!isEligible) {
        const limitedLabel = document.createElement("div");
        limitedLabel.textContent = "RESTRICTED";
        Object.assign(limitedLabel.style, {
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -70%)",
          fontSize: "22px",
          fontWeight: "400",
          color: "#e8e4dc",
          fontFamily: '"Jersey 20", sans-serif',
          textAlign: "center",
          lineHeight: "1.1",
          letterSpacing: "1px",
          whiteSpace: "pre-line",
          textShadow: "0 2px 6px rgba(0,0,0,0.8)",
          pointerEvents: "none",
        });
        card.appendChild(limitedLabel);
      }

      // Character sprite
      const charId = candidate.characterId || 0;
      if (charId > 0) {
        const charImg = document.createElement("img");
        charImg.src = `assets/character${charId}.png`;
        charImg.alt = candidate.name;
        charImg.draggable = false;
        Object.assign(charImg.style, {
          width: "90px",
          height: "auto",
          objectFit: "contain",
          imageRendering: "pixelated",
          pointerEvents: "none",
          marginBottom: "20px",
        });
        card.appendChild(charImg);
      }

      // Player name
      const name = document.createElement("div");
      name.textContent = candidate.name;
      Object.assign(name.style, {
        fontSize: "22px",
        color: "#514b3f",
        fontFamily: '"Jersey 20", sans-serif',
        position: "relative",
        zIndex: "1",
      });
      card.appendChild(name);

      // Role label (only shown if provided, e.g. exploiter sees other exploiters)
      const roleLabel = document.createElement("div");
      roleLabel.textContent = candidate.roleLabel || "";
      Object.assign(roleLabel.style, {
        fontSize: "18px",
        color: candidate.roleColor || "#514b3f",
        fontFamily: '"Jersey 20", sans-serif',
        letterSpacing: candidate.roleLabel ? "1px" : "0",
        minHeight: "22px",
        position: "relative",
        zIndex: "1",
      });
      card.appendChild(roleLabel);

      if (isEligible) {
        card.addEventListener("click", () => {
          this.selectedIndex = idx;
          this.updateCardSelection(cardEls);
        });
      }

      cardEls.push(card);
      cardRow.appendChild(card);
    });

    panel.appendChild(cardRow);

    // ── Confirm button ──────────────────────────────────────────────
    const confirmRow = document.createElement("div");
    Object.assign(confirmRow.style, {
      width: "100%",
      display: "flex",
      justifyContent: "center",
    });

    const confirmBtn = document.createElement("button");
    confirmBtn.textContent = "CONFIRM";
    Object.assign(confirmBtn.style, {
      fontFamily: '"Jersey 20", sans-serif',
      fontSize: "32px",
      fontWeight: "400",
      letterSpacing: "2px",
      color: "#f0ebe3",
      background: "#7a6a52",
      border: "4px solid #bfa76a",
      padding: "12px 52px",
      cursor: "pointer",
      boxShadow: "4px 4px 0 #3a3228",
      transition: "none",
      imageRendering: "pixelated",
    });

    confirmBtn.addEventListener("mousedown", () => {
      confirmBtn.style.transform = "translateX(4px) translateY(4px)";
      confirmBtn.style.boxShadow = "0 0 0 #3a3228";
    });
    confirmBtn.addEventListener("mouseup", () => {
      confirmBtn.style.transform = "translateX(0) translateY(0)";
      confirmBtn.style.boxShadow = "4px 4px 0 #3a3228";
    });
    confirmBtn.addEventListener("mouseleave", () => {
      confirmBtn.style.transform = "translateX(0) translateY(0)";
      confirmBtn.style.boxShadow = "4px 4px 0 #3a3228";
    });

    confirmBtn.addEventListener("click", () => {
      if (this.selectedIndex === null) return;
      const chosen = this.candidates[this.selectedIndex];
      this.events.emit("nomination-confirmed", chosen.name, this.selectedIndex);
      this.hide();
    });

    confirmRow.appendChild(confirmBtn);
    panel.appendChild(confirmRow);

    overlay.appendChild(panel);

    parent.appendChild(overlay);
    this.overlayEl = overlay;

    // ── Inject styles ───────────────────────────────────────────────
    const style = document.createElement("style");
    style.textContent = `
      #nomination-overlay * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }
      #nomination-overlay button:hover {
        filter: brightness(1.12);
      }
      #nomination-overlay .nom-card.selected {
        outline: 4px solid #d4a843;
        outline-offset: 0px;
      }
    `;
    document.head.appendChild(style);
    this.injectedStyleEl = style;
  }

  // ─── HELPERS ──────────────────────────────────────────────────────

  private updateCardSelection(cards: HTMLDivElement[]) {
    cards.forEach((card, idx) => {
      card.classList.toggle("selected", idx === this.selectedIndex);
    });
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
    if (this.keyHandler) {
      window.removeEventListener("keydown", this.keyHandler);
      this.keyHandler = undefined;
    }
  }
}