import Phaser from "phaser";

const ASSET_CONTEXT = "assets/context.png";

// Same dimensions as policy_desc.png
const ASSET_W = 1060;
const ASSET_H = 740;

interface ContextData {
  title?: string;
  context?: string;
}

export class ContextScene extends Phaser.Scene {
  private overlayEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;
  private visible: boolean = false;

  private contextTitle: string = "";
  private contextText: string = "";

  // DOM refs for live updates
  private titleEl?: HTMLDivElement;
  private textEl?: HTMLDivElement;

  constructor() {
    super({ key: "ContextScene" });
  }

  init(data: ContextData) {
    if (data.title !== undefined) this.contextTitle = data.title;
    if (data.context !== undefined) this.contextText = data.context;
  }

  preload() {
    if (!this.textures.exists("context_bg")) {
      this.load.image("context_bg", ASSET_CONTEXT);
    }
  }

  create() {
    this.cameras.main.setVisible(false);

    this.buildOverlay();

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);
  }

  // ─── PUBLIC SHOW/HIDE ─────────────────────────────────────────────

  public show(data?: ContextData) {
    if (data?.title !== undefined) this.contextTitle = data.title;
    if (data?.context !== undefined) this.contextText = data.context;
    this.updateContent();
    this.visible = true;
    if (this.overlayEl) this.overlayEl.style.display = "flex";
  }

  public hide() {
    this.visible = false;
    if (this.overlayEl) this.overlayEl.style.display = "none";
  }

  private updateContent() {
    if (this.titleEl) this.titleEl.textContent = this.contextTitle;
    if (this.textEl) this.textEl.textContent = this.contextText;
  }

  // ─── BUILD DOM ────────────────────────────────────────────────────

  private buildOverlay() {
    const existing = document.getElementById("context-overlay");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    // ── Full-screen backdrop ────────────────────────────────────────
    const overlay = document.createElement("div");
    overlay.id = "context-overlay";
    Object.assign(overlay.style, {
      position: "fixed",
      inset: "0",
      display: "none",
      alignItems: "center",
      justifyContent: "center",
      zIndex: "600",
      background: "rgba(0, 0, 0, 0.75)",
      fontFamily: '"Jersey 20", sans-serif',
      imageRendering: "pixelated",
    });

    // ── Folder container — maintains aspect ratio ───────────────────
    const folder = document.createElement("div");
    Object.assign(folder.style, {
      position: "relative",
      width: "90%",
      maxWidth: "850px",
      aspectRatio: `${ASSET_W} / ${ASSET_H}`,
      backgroundImage: `url("${ASSET_CONTEXT}")`,
      backgroundSize: "contain",
      backgroundRepeat: "no-repeat",
      backgroundPosition: "center",
      imageRendering: "pixelated",
    });

    // ── Single page — spans both sides of the folder ────────────────
    const page = document.createElement("div");
    page.classList.add("context-page");
    Object.assign(page.style, {
      position: "absolute",
      left: "3%",
      top: "8%",
      width: "90%",
      height: "82%",
      display: "flex",
      flexDirection: "column",
      alignItems: "flex-start",
      justifyContent: "flex-start",
      padding: "4% 5%",
      boxSizing: "border-box",
      overflowY: "auto",
      overflowX: "hidden",
    });

    // ── Title ───────────────────────────────────────────────────────
    const titleEl = document.createElement("div");
    titleEl.textContent = this.contextTitle;
    Object.assign(titleEl.style, {
      fontSize: "clamp(20px, 3vw, 36px)",
      fontWeight: "400",
      color: "#3a3228",
      fontFamily: '"Jersey 20", sans-serif',
      textAlign: "left",
      letterSpacing: "2px",
      lineHeight: "1.2",
      wordBreak: "break-word",
      marginBottom: "16px",
      width: "100%",
    });
    page.appendChild(titleEl);
    this.titleEl = titleEl;

    // ── Context text ────────────────────────────────────────────────
    const textEl = document.createElement("div");
    textEl.textContent = this.contextText;
    Object.assign(textEl.style, {
      fontSize: "clamp(12px, 1.7vw, 20px)",
      fontWeight: "400",
      color: "#3a3228",
      fontFamily: '"Jersey 20", sans-serif',
      textAlign: "left",
      lineHeight: "1.35",
      letterSpacing: "0.5px",
      wordBreak: "break-word",
    });
    page.appendChild(textEl);
    this.textEl = textEl;

    folder.appendChild(page);

    // ── Close (X) button — top-right of folder ──────────────────────
    const closeBtn = document.createElement("button");
    closeBtn.textContent = "X";
    Object.assign(closeBtn.style, {
      position: "absolute",
      top: "-18px",
      right: "-18px",
      width: "40px",
      height: "40px",
      background: "#842929",
      border: "4px solid #bc6262",
      borderRadius: "4px",
      color: "#e8e4dc",
      fontSize: "22px",
      fontFamily: '"Jersey 20", sans-serif',
      cursor: "pointer",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "0",
      lineHeight: "1",
      boxShadow: "3px 3px 0 #000000",
      imageRendering: "pixelated",
      zIndex: "1",
    });
    closeBtn.addEventListener("click", () => {
      this.hide();
    });
    folder.appendChild(closeBtn);

    overlay.appendChild(folder);

    parent.appendChild(overlay);
    this.overlayEl = overlay;

    // ── Inject styles ───────────────────────────────────────────────
    const style = document.createElement("style");
    style.textContent = `
      #context-overlay * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }
      #context-overlay button:hover {
        filter: brightness(1.2);
      }
      /* Themed scrollbar */
      .context-page::-webkit-scrollbar {
        width: 8px;
      }
      .context-page::-webkit-scrollbar-track {
        background: rgba(58, 50, 40, 0.1);
        border-radius: 4px;
      }
      .context-page::-webkit-scrollbar-thumb {
        background: rgba(58, 50, 40, 0.35);
        border-radius: 4px;
      }
      .context-page::-webkit-scrollbar-thumb:hover {
        background: rgba(58, 50, 40, 0.55);
      }
      .context-page {
        scrollbar-width: thin;
        scrollbar-color: rgba(58, 50, 40, 0.35) rgba(58, 50, 40, 0.1);
      }
    `;
    document.head.appendChild(style);
    this.injectedStyleEl = style;
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
    this.titleEl = undefined;
    this.textEl = undefined;
  }
}