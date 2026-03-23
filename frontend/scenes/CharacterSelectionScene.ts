import Phaser from "phaser";

const ASSETS = {
  player_basecard: "assets/player_basecard.png",
};

const CHARACTER_COUNT = 8;

interface CharacterSelectionData {
  username?: string;
}

export class CharacterSelectionScene extends Phaser.Scene {
  private overlayEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;
  private visible: boolean = false;
  private keyHandler?: (e: KeyboardEvent) => void;

  private username: string = "";
  private selectedIndex: number | null = null;

  constructor() {
    super({ key: "CharacterSelectionScene" });
  }

  init(data: CharacterSelectionData) {
    if (data.username) this.username = data.username;
  }

  preload() {
    // Load all 8 character sprites
    for (let i = 1; i <= CHARACTER_COUNT; i++) {
      const key = `character${i}`;
      if (!this.textures.exists(key)) {
        this.load.image(key, `assets/character${i}.png`);
      }
    }
    if (!this.textures.exists("player_basecard")) {
      this.load.image("player_basecard", ASSETS.player_basecard);
    }
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

  // ─── PUBLIC SHOW/HIDE ───────────────────────────────────────────

  public show(data?: CharacterSelectionData) {
    if (data?.username) this.username = data.username;
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
    const existing = document.getElementById("character-selection-overlay");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    // ── Full-screen backdrop ────────────────────────────────────────
    const overlay = document.createElement("div");
    overlay.id = "character-selection-overlay";
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
      borderRadius: "4px",
      border: "4px solid #4a4e55",
      padding: "36px 44px 40px",
      maxWidth: "900px",
      width: "92%",
      boxSizing: "border-box",
      display: "flex",
      flexDirection: "column",
      alignItems: "flex-start",
      gap: "0px",
      boxShadow: "6px 6px 0 #000000",
      imageRendering: "pixelated",
      maxHeight: "90vh",
      overflowY: "auto",
    });

    // ── Title ───────────────────────────────────────────────────────
    const title = document.createElement("div");
    title.textContent = "SELECT CHARACTER";
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
    desc.textContent = "Choose your representative for the session.";
    Object.assign(desc.style, {
      fontSize: "24px",
      color: "#9e9a92",
      fontFamily: '"Jersey 20", sans-serif',
      lineHeight: "1.3",
      marginBottom: "24px",
    });
    panel.appendChild(desc);

    // ── Character cards grid ────────────────────────────────────────
    const cardGrid = document.createElement("div");
    Object.assign(cardGrid.style, {
      display: "flex",
      gap: "18px",
      width: "100%",
      justifyContent: "center",
      flexWrap: "wrap",
      marginBottom: "28px",
    });

    const cardEls: HTMLDivElement[] = [];

    for (let i = 1; i <= CHARACTER_COUNT; i++) {
      const idx = i - 1;

      const card = document.createElement("div");
      card.classList.add("char-card");
      card.dataset.index = String(idx);

      // Card container — basecard as background
      Object.assign(card.style, {
        width: "130px",
        height: "190px",
        backgroundImage: `url("${ASSETS.player_basecard}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        boxSizing: "border-box",
        overflow: "hidden",
        imageRendering: "pixelated",
        cursor: "pointer",
        position: "relative",
      });

      // Character sprite — sits in the grey area of the basecard
      // Original character is 60×80; the grey area on a 130×190 card
      // is roughly the top ~65% portion. We scale the character to fill nicely.
      const charImg = document.createElement("img");
      charImg.src = `assets/character${i}.png`;
      charImg.alt = `Character ${i}`;
      charImg.draggable = false;
      Object.assign(charImg.style, {
        width: "84px",
        height: "112px", // maintains 60:80 aspect ratio
        objectFit: "contain",
        imageRendering: "pixelated",
        marginTop: "11px",
        pointerEvents: "none",
        position: "relative",
        zIndex: "1",
      });
      card.appendChild(charImg);

      card.addEventListener("click", () => {
        this.selectedIndex = idx;
        this.updateCardSelection(cardEls);
      });

      cardEls.push(card);
      cardGrid.appendChild(card);
    }

    panel.appendChild(cardGrid);

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
      borderRadius: "4px",
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
      const characterNumber = this.selectedIndex + 1;
      this.events.emit("character-selected", characterNumber, this.username);
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
      #character-selection-overlay * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }
      #character-selection-overlay button:hover {
        filter: brightness(1.12);
      }
      #character-selection-overlay .char-card {
        transition: none;
      }
      #character-selection-overlay .char-card:hover {
        outline: 3px solid #9e9a92;
        outline-offset: 0px;
      }
      #character-selection-overlay .char-card.selected {
        outline: 4px solid #d4a843;
        outline-offset: 0px;
      }
      #character-selection-overlay .char-card.selected:hover {
        outline: 4px solid #d4a843;
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