import Phaser from "phaser";

const ASSET_POLICY_DESC = "assets/policy_desc.png";

// Native resolution of the asset
const ASSET_W = 1060;
const ASSET_H = 740;

interface PolicyDescData {
  title?: string;
  description?: string;
}

export class PolicyDescScene extends Phaser.Scene {
  private overlayEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;
  private visible: boolean = false;
  private keyHandler?: (e: KeyboardEvent) => void;

  private policyTitle: string = "";
  private policyDescription: string = "";

  // DOM refs for live updates
  private titleEl?: HTMLDivElement;
  private descEl?: HTMLDivElement;

  constructor() {
    super({ key: "PolicyDescScene" });
  }

  init(data: PolicyDescData) {
    if (data.title !== undefined) this.policyTitle = data.title;
    if (data.description !== undefined) this.policyDescription = data.description;
  }

  preload() {
    if (!this.textures.exists("policy_desc")) {
      this.load.image("policy_desc", ASSET_POLICY_DESC);
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

  // ─── PUBLIC SHOW/HIDE ─────────────────────────────────────────────

  public show(data?: PolicyDescData) {
    if (data?.title !== undefined) this.policyTitle = data.title;
    if (data?.description !== undefined) this.policyDescription = data.description;
    this.updateContent();
    this.visible = true;
    if (this.overlayEl) this.overlayEl.style.display = "flex";
  }

  public hide() {
    this.visible = false;
    if (this.overlayEl) this.overlayEl.style.display = "none";
  }

  public setPolicy(title: string, description: string) {
    this.policyTitle = title;
    this.policyDescription = description;
    this.updateContent();
  }

  private updateContent() {
    if (this.titleEl) this.titleEl.textContent = this.policyTitle;
    if (this.descEl) this.descEl.textContent = this.policyDescription;
  }

  // ─── BUILD DOM ────────────────────────────────────────────────────

  private buildOverlay() {
    const existing = document.getElementById("policy-desc-overlay");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    // ── Full-screen backdrop ────────────────────────────────────────
    const overlay = document.createElement("div");
    overlay.id = "policy-desc-overlay";
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
      backgroundImage: `url("${ASSET_POLICY_DESC}")`,
      backgroundSize: "contain",
      backgroundRepeat: "no-repeat",
      backgroundPosition: "center",
      imageRendering: "pixelated",
    });

    // ── Left page — TITLE ───────────────────────────────────────────
    const leftPage = document.createElement("div");
    Object.assign(leftPage.style, {
      position: "absolute",
      left: "3%",
      top: "8%",
      width: "42%",
      height: "82%",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      padding: "6% 5%",
      boxSizing: "border-box",
      overflow: "hidden",
    });

    const titleEl = document.createElement("div");
    titleEl.textContent = this.policyTitle;
    Object.assign(titleEl.style, {
      fontSize: "clamp(22px, 3.5vw, 42px)",
      fontWeight: "400",
      color: "#3a3228",
      fontFamily: '"Jersey 20", sans-serif',
      textAlign: "center",
      letterSpacing: "2px",
      lineHeight: "1.2",
      wordBreak: "break-word",
    });
    leftPage.appendChild(titleEl);
    this.titleEl = titleEl;

    folder.appendChild(leftPage);

    // ── Right page — DESCRIPTION (scrollable) ───────────────────────
    const rightPage = document.createElement("div");
    rightPage.classList.add("policy-desc-right-page");
    Object.assign(rightPage.style, {
      position: "absolute",
      left: "50%",
      top: "8%",
      width: "42%",
      height: "82%",
      display: "flex",
      flexDirection: "column",
      alignItems: "flex-start",
      justifyContent: "flex-start",
      padding: "4% 4%",
      boxSizing: "border-box",
      overflowY: "auto",
      overflowX: "hidden",
    });

    const descEl = document.createElement("div");
    descEl.textContent = this.policyDescription;
    Object.assign(descEl.style, {
      fontSize: "clamp(11px, 1.6vw, 20px)",
      fontWeight: "400",
      color: "#3a3228",
      fontFamily: '"Jersey 20", sans-serif',
      textAlign: "left",
      lineHeight: "1.3",
      letterSpacing: "0.5px",
      wordBreak: "break-word",
    });
    rightPage.appendChild(descEl);
    this.descEl = descEl;

    folder.appendChild(rightPage);

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
      #policy-desc-overlay * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }
      #policy-desc-overlay button:hover {
        filter: brightness(1.2);
      }
      /* Themed scrollbar for the right page */
      .policy-desc-right-page::-webkit-scrollbar {
        width: 8px;
      }
      .policy-desc-right-page::-webkit-scrollbar-track {
        background: rgba(58, 50, 40, 0.1);
        border-radius: 4px;
      }
      .policy-desc-right-page::-webkit-scrollbar-thumb {
        background: rgba(58, 50, 40, 0.35);
        border-radius: 4px;
      }
      .policy-desc-right-page::-webkit-scrollbar-thumb:hover {
        background: rgba(58, 50, 40, 0.55);
      }
      /* Firefox scrollbar */
      .policy-desc-right-page {
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
    if (this.keyHandler) {
      window.removeEventListener("keydown", this.keyHandler);
      this.keyHandler = undefined;
    }
    this.titleEl = undefined;
    this.descEl = undefined;
  }
}