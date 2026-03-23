import Phaser from "phaser";

const ASSETS = {
  player_basecard: "assets/player_basecard.png",
};

interface VotingData {
  nominatorName?: string;
  nomineeName?: string;
  nomineeCharacterId?: number;
}

export class VotingScene extends Phaser.Scene {
  private overlayEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;
  private visible: boolean = false;
  private keyHandler?: (e: KeyboardEvent) => void;

  // Data passed in via scene launch
  private nominatorName: string = "Player 1";
  private nomineeName: string = "Player 2";
  private nomineeCharacterId: number = 0;
  private selectedVote: "aye" | "nay" | null = null;

  constructor() {
    super({ key: "VotingScene" });
  }

  init(data: VotingData) {
    if (data.nominatorName) this.nominatorName = data.nominatorName;
    if (data.nomineeName) this.nomineeName = data.nomineeName;
    if (data.nomineeCharacterId) this.nomineeCharacterId = data.nomineeCharacterId;
  }

  create() {
    // Don't render anything on the Phaser canvas
    this.cameras.main.setVisible(false);

    // Build DOM overlay (starts hidden)
    this.buildOverlay();

    // Toggle with V key
    this.keyHandler = (e: KeyboardEvent) => {
      if (e.key === "v" || e.key === "V") {
        this.toggleOverlay();
      }
    };
    window.addEventListener("keydown", this.keyHandler);

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

  public show(data?: VotingData) {
    if (data?.nominatorName) this.nominatorName = data.nominatorName;
    if (data?.nomineeName) this.nomineeName = data.nomineeName;
    if (data?.nomineeCharacterId !== undefined) this.nomineeCharacterId = data.nomineeCharacterId;
    this.selectedVote = null;
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
    // Clean previous
    const existing = document.getElementById("voting-overlay");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    // ── Full-screen backdrop ────────────────────────────────────────
    const overlay = document.createElement("div");
    overlay.id = "voting-overlay";
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
      maxWidth: "680px",
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
    title.textContent = "VOTING";
    Object.assign(title.style, {
      fontSize: "42px",
      fontWeight: "400",
      color: "#e8e4dc",
      letterSpacing: "2px",
      marginBottom: "20px",
      fontFamily: '"Jersey 20", sans-serif',
    });
    panel.appendChild(title);

    // ── Nominee row (card + description) ────────────────────────────
    const nomineeRow = document.createElement("div");
    Object.assign(nomineeRow.style, {
      display: "flex",
      alignItems: "center",
      gap: "24px",
      marginBottom: "28px",
      width: "100%",
    });

    // Nominee card using player_basecard asset
    const cardWrap = document.createElement("div");
    Object.assign(cardWrap.style, {
      width: "120px",
      height: "175px",
      backgroundImage: `url("${ASSETS.player_basecard}")`,
      backgroundSize: "cover",
      backgroundPosition: "center",
      backgroundRepeat: "no-repeat",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "flex-end",
      paddingBottom: "12px",
      boxSizing: "border-box",
      flexShrink: "0",
      overflow: "hidden",
      imageRendering: "pixelated",
    });

    // Character sprite (if available)
    if (this.nomineeCharacterId > 0) {
      const charImg = document.createElement("img");
      charImg.src = `assets/character${this.nomineeCharacterId}.png`;
      charImg.alt = this.nomineeName;
      charImg.draggable = false;
      Object.assign(charImg.style, {
        width: "70px",
        height: "93px",
        objectFit: "contain",
        imageRendering: "pixelated",
        pointerEvents: "none",
        marginBottom: "25px",
      });
      cardWrap.appendChild(charImg);
    }

    const cardName = document.createElement("div");
    cardName.textContent = this.nomineeName;
    Object.assign(cardName.style, {
      fontSize: "24px",
      color: "#514b3f",
      fontFamily: '"Jersey 20", sans-serif',
    });
    cardWrap.appendChild(cardName);
    nomineeRow.appendChild(cardWrap);

    // Description text
    const descWrap = document.createElement("div");
    Object.assign(descWrap.style, {
      display: "flex",
      flexDirection: "column",
      gap: "8px",
    });

    const descLine1 = document.createElement("div");
    descLine1.textContent = `${this.nominatorName} has nominated ${this.nomineeName} as Vice.`;
    Object.assign(descLine1.style, {
      fontSize: "26px",
      color: "#e8e4dc",
      fontFamily: '"Jersey 20", sans-serif',
      lineHeight: "1.3",
    });

    const descLine2 = document.createElement("div");
    descLine2.textContent =
      "Vote on whether you want this government to proceed; The vote passes if over 50% of the votes are yes.";
    Object.assign(descLine2.style, {
      fontSize: "22px",
      color: "#9e9a92",
      fontFamily: '"Jersey 20", sans-serif',
      lineHeight: "1.3",
    });

    descWrap.appendChild(descLine1);
    descWrap.appendChild(descLine2);
    nomineeRow.appendChild(descWrap);
    panel.appendChild(nomineeRow);

    // ── Vote buttons row ────────────────────────────────────────────
    const btnRow = document.createElement("div");
    Object.assign(btnRow.style, {
      display: "flex",
      gap: "28px",
      width: "100%",
      justifyContent: "center",
      marginBottom: "28px",
    });

    const ayeBtn = this.buildVoteButton("AYE", "#2b6e3f", "#1a4a2a", "aye");
    const nayBtn = this.buildVoteButton("NAY", "#8b2d2d", "#5a1a1a", "nay");

    // Wire up selection
    ayeBtn.addEventListener("click", () => {
      this.selectedVote = "aye";
      this.updateButtonStates(ayeBtn, nayBtn);
    });
    nayBtn.addEventListener("click", () => {
      this.selectedVote = "nay";
      this.updateButtonStates(ayeBtn, nayBtn);
    });

    btnRow.appendChild(ayeBtn);
    btnRow.appendChild(nayBtn);
    panel.appendChild(btnRow);

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
      if (!this.selectedVote) return;
      // Emit event so game logic can handle the vote
      this.events.emit("vote-confirmed", this.selectedVote);
      this.hide();
    });

    confirmRow.appendChild(confirmBtn);
    panel.appendChild(confirmRow);

    overlay.appendChild(panel);

    parent.appendChild(overlay);
    this.overlayEl = overlay;

    // Inject hover style
    const style = document.createElement("style");
    style.textContent = `
      #voting-overlay * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }
      #voting-overlay button:hover {
        filter: brightness(1.12);
      }
      #voting-overlay .vote-btn.selected {
        outline: 4px solid #d4a843;
        outline-offset: 0px;
      }
    `;
    document.head.appendChild(style);
    this.injectedStyleEl = style;
  }

  // ─── HELPERS ──────────────────────────────────────────────────────

  private buildVoteButton(
    label: string,
    bgColor: string,
    shadow: string,
    _value: "aye" | "nay"
  ): HTMLButtonElement {
    const btn = document.createElement("button");
    btn.classList.add("vote-btn");
    btn.textContent = label;
    Object.assign(btn.style, {
      flex: "1",
      fontFamily: '"Jersey 20", sans-serif',
      fontSize: "36px",
      fontWeight: "400",
      textTransform: "uppercase",
      letterSpacing: "2px",
      color: "#f0ebe3",
      background: bgColor,
      border: `4px solid ${bgColor}`,
      padding: "18px 0",
      cursor: "pointer",
      boxShadow: `4px 4px 0 ${shadow}`,
      transition: "none",
      imageRendering: "pixelated",
    });

    btn.addEventListener("mousedown", () => {
      btn.style.transform = "translateX(4px) translateY(4px)";
      btn.style.boxShadow = `0 0 0 ${shadow}`;
    });
    btn.addEventListener("mouseup", () => {
      btn.style.transform = "translateX(0) translateY(0)";
      btn.style.boxShadow = `4px 4px 0 ${shadow}`;
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "translateX(0) translateY(0)";
      btn.style.boxShadow = `4px 4px 0 ${shadow}`;
    });

    return btn;
  }

  private updateButtonStates(ayeBtn: HTMLButtonElement, nayBtn: HTMLButtonElement) {
    ayeBtn.classList.toggle("selected", this.selectedVote === "aye");
    nayBtn.classList.toggle("selected", this.selectedVote === "nay");
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