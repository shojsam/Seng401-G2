import Phaser from "phaser";

const ASSET_POLICY_FOLDER = "assets/policy_folder1.png";

// Native resolution of the policy card asset
const CARD_W = 56;
const CARD_H = 74;

interface PolicyInfo {
  title: string;
  description: string;
}

interface PolicyEnactData {
  policies?: PolicyInfo[];
}

export class PolicyEnactScene extends Phaser.Scene {
  private overlayEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;
  private visible: boolean = false;
  private keyHandler?: (e: KeyboardEvent) => void;

  private policies: PolicyInfo[] = [
    { title: "CARBON TAX", description: "Impose a tax on carbon emissions from major industrial polluters. Revenue is redirected toward renewable energy infrastructure." },
    { title: "DEFORESTATION PERMIT", description: "Grant logging companies expanded access to protected forests in exchange for short-term economic growth." },
  ];

  constructor() {
    super({ key: "PolicyEnactScene" });
  }

  init(data: PolicyEnactData) {
    if (data.policies && data.policies.length > 0) {
      this.policies = data.policies;
    }
  }

  preload() {
    if (!this.textures.exists("policy_folder")) {
      this.load.image("policy_folder", ASSET_POLICY_FOLDER);
    }
  }

  create() {
    this.cameras.main.setVisible(false);

    this.buildOverlay();

    this.keyHandler = (e: KeyboardEvent) => {
      if (e.key === "e" || e.key === "E") {
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

  // ─── PUBLIC SHOW/HIDE ─────────────────────────────────────────────

  public show(data?: PolicyEnactData) {
    if (data?.policies && data.policies.length > 0) {
      this.policies = data.policies;
      this.buildOverlay();
    }
    this.visible = true;
    if (this.overlayEl) this.overlayEl.style.display = "flex";
  }

  public hide() {
    this.visible = false;
    if (this.overlayEl) this.overlayEl.style.display = "none";
  }

  // ─── BUILD DOM ────────────────────────────────────────────────────

  private buildOverlay() {
    const existing = document.getElementById("policy-enact-overlay");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    // ── Full-screen backdrop ────────────────────────────────────────
    const overlay = document.createElement("div");
    overlay.id = "policy-enact-overlay";
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
    title.textContent = "ENACT A POLICY";
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
    desc.textContent = "Review the remaining policies and choose one to enact. Click a policy to read its details.";
    Object.assign(desc.style, {
      fontSize: "24px",
      color: "#9e9a92",
      fontFamily: '"Jersey 20", sans-serif',
      lineHeight: "1.3",
      marginBottom: "28px",
    });
    panel.appendChild(desc);

    // ── Policy cards row ────────────────────────────────────────────
    const cardRow = document.createElement("div");
    Object.assign(cardRow.style, {
      display: "flex",
      gap: "32px",
      width: "100%",
      justifyContent: "center",
      flexWrap: "wrap",
      marginBottom: "28px",
    });

    const scale = 2.75;
    const displayW = Math.floor(CARD_W * scale);
    const displayH = Math.floor(CARD_H * scale);

    this.policies.forEach((policy, idx) => {
      // Column wrapper for card + button
      const col = document.createElement("div");
      Object.assign(col.style, {
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "16px",
      });

      // ── Policy card ─────────────────────────────────────────────
      const card = document.createElement("div");
      card.classList.add("enact-card");
      Object.assign(card.style, {
        width: `${displayW}px`,
        height: `${displayH}px`,
        backgroundImage: `url("${ASSET_POLICY_FOLDER}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        imageRendering: "pixelated",
        cursor: "pointer",
        position: "relative",
        boxSizing: "border-box",
      });

      // Click card → open PolicyDescScene with this policy's info
      card.addEventListener("click", () => {
        this.openPolicyDesc(policy);
      });

      col.appendChild(card);

      // ── Enact button ────────────────────────────────────────────
      const enactBtn = document.createElement("button");
      enactBtn.textContent = "ENACT";
      Object.assign(enactBtn.style, {
        fontFamily: '"Jersey 20", sans-serif',
        fontSize: "24px",
        fontWeight: "400",
        letterSpacing: "2px",
        color: "#f0ebe3",
        background: "#66785a",
        border: "4px solid #809671",
        borderRadius: "4px",
        padding: "8px 24px",
        cursor: "pointer",
        boxShadow: "4px 4px 0 #2e3a26",
        transition: "none",
        imageRendering: "pixelated",
        width: `${displayW}px`,
        boxSizing: "border-box",
      });

      enactBtn.addEventListener("mousedown", () => {
        enactBtn.style.transform = "translateX(4px) translateY(4px)";
        enactBtn.style.boxShadow = "0 0 0 #2e3a26";
      });
      enactBtn.addEventListener("mouseup", () => {
        enactBtn.style.transform = "translateX(0) translateY(0)";
        enactBtn.style.boxShadow = "4px 4px 0 #2e3a26";
      });
      enactBtn.addEventListener("mouseleave", () => {
        enactBtn.style.transform = "translateX(0) translateY(0)";
        enactBtn.style.boxShadow = "4px 4px 0 #2e3a26";
      });

      enactBtn.addEventListener("click", () => {
        this.events.emit("policy-enacted", policy, idx);
      });

      col.appendChild(enactBtn);
      cardRow.appendChild(col);
    });

    panel.appendChild(cardRow);

    // ── Hint ────────────────────────────────────────────────────────
    const hint = document.createElement("div");
    hint.textContent = "Press E to close";
    Object.assign(hint.style, {
      fontSize: "18px",
      color: "#6b6860",
      fontFamily: '"Jersey 20", sans-serif',
      width: "100%",
      textAlign: "center",
    });
    panel.appendChild(hint);

    overlay.appendChild(panel);

    // Click backdrop to close
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) this.hide();
    });

    parent.appendChild(overlay);
    this.overlayEl = overlay;

    // ── Inject styles ───────────────────────────────────────────────
    const style = document.createElement("style");
    style.textContent = `
      #policy-enact-overlay * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }
      #policy-enact-overlay .enact-card:hover {
        outline: 3px solid #d4a843;
        outline-offset: 0px;
      }
      #policy-enact-overlay button:hover {
        filter: brightness(1.12);
      }
    `;
    document.head.appendChild(style);
    this.injectedStyleEl = style;
  }

  // ─── HELPERS ──────────────────────────────────────────────────────

  private openPolicyDesc(policy: PolicyInfo) {
    const policyDescScene = this.scene.get("PolicyDescScene");
    if (policyDescScene && policyDescScene.scene.isActive()) {
      (policyDescScene as { show: (data: { title: string; description: string }) => void }).show({
        title: policy.title,
        description: policy.description,
      });
    }
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