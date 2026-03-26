/**
 * scenes/GameOverScene.ts — Full-screen game-over results scene.
 *
 * Displays:
 *   1. Winner banner (REFORMERS WIN / EXPLOITERS WIN)
 *   2. Player character cards with revealed roles
 *   3. Enacted policy holders (sustainable + exploitative) — clickable
 *   4. Back to Main Menu button
 *
 * Uses PolicyDescScene and ContextScene as overlay scenes (same as
 * BoardGameScene) for viewing policy details and context.
 *
 * This is a standalone scene (not an overlay) that replaces the board.
 */
import Phaser from "phaser";

const ASSETS = {
  player_basecard: "assets/player_basecard.png",
  policy_folder: "assets/policy_folder1.png",
};

interface PlayerInfo {
  name: string;
  role: string;
  characterId: number;
}

interface PolicyInfo {
  title: string;
  description: string;
  policy_type: "sustainable" | "exploitative";
  hover?: string;
}

export interface GameOverData {
  winner: string;
  players: PlayerInfo[];
  enactedSustainable: PolicyInfo[];
  enactedExploitative: PolicyInfo[];
}

export class GameOverScene extends Phaser.Scene {
  private containerEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;

  private winner = "reformers";
  private players: PlayerInfo[] = [];
  private enactedSustainable: PolicyInfo[] = [];
  private enactedExploitative: PolicyInfo[] = [];

  constructor() {
    super({ key: "GameOverScene" });
  }

  init(data: GameOverData) {
    this.winner = data.winner || "reformers";
    this.players = data.players || [];
    this.enactedSustainable = data.enactedSustainable || [];
    this.enactedExploitative = data.enactedExploitative || [];
  }

  create() {
    if (this.game.canvas) {
      this.game.canvas.style.display = "none";
    }

    // Reset game-container so it doesn't keep the board's large fixed height
    const gameContainer = document.getElementById("game-container");
    if (gameContainer) {
      gameContainer.style.width = "100%";
      gameContainer.style.height = "";
      gameContainer.style.minHeight = "100vh";
      gameContainer.style.overflow = "visible";
    }

    // Ensure only one scrollbar — the body's
    document.body.style.overflowX = "hidden";
    document.body.style.overflowY = "auto";
    document.documentElement.style.overflowX = "hidden";
    document.documentElement.style.overflowY = "auto";

    this.buildScene();

    // Launch overlay scenes after a short delay so Phaser has time
    // to fully stop them if BoardGameScene's cleanup just ran.
    this.time.delayedCall(100, () => {
      this.launchOverlayScenes();
    });

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);
  }

  // ─── OVERLAY SCENE LAUNCHES ───────────────────────────────────

  private launchOverlayScenes() {
    if (this.scene.isActive("PolicyDescScene")) this.scene.stop("PolicyDescScene");
    if (this.scene.isActive("ContextScene")) this.scene.stop("ContextScene");

    this.scene.launch("PolicyDescScene", { title: "", description: "" });
    this.scene.launch("ContextScene", { title: "", context: "" });
  }

  private openPolicyDesc(title: string, description: string) {
    const s = this.scene.get("PolicyDescScene");
    if (s && s.scene.isActive()) {
      (s as unknown as { show: (d: { title: string; description: string }) => void }).show({
        title,
        description,
      });
    }
  }

  private openContext(title: string, hover: string) {
    const s = this.scene.get("ContextScene");
    if (s && s.scene.isActive()) {
      (s as unknown as { show: (d: { title: string; context: string }) => void }).show({
        title,
        context: hover || "No context available for this policy yet.",
      });
    }
  }

  // ─── BUILD SCENE ──────────────────────────────────────────────

  private buildScene() {
    const existing = document.getElementById("game-over-scene");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;
    const isReformers = this.winner === "reformers";
    const accentColor = isReformers ? "#66785a" : "#842929";
    const accentBorder = isReformers ? "#809671" : "#bc6262";

    const container = document.createElement("div");
    container.id = "game-over-scene";
    Object.assign(container.style, {
      position: "relative",
      width: "100%",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "flex-start",
      fontFamily: '"Jersey 20", sans-serif',
      color: "#f4efe7",
      boxSizing: "border-box",
      imageRendering: "pixelated",
    });

    // Background
    const bgBase = document.createElement("div");
    Object.assign(bgBase.style, { position: "absolute", inset: "0", background: "#5c3d2e", zIndex: "0" });
    container.appendChild(bgBase);

    const bgTexture = document.createElement("div");
    Object.assign(bgTexture.style, {
      position: "absolute", inset: "0", zIndex: "1", pointerEvents: "none",
      background: "repeating-linear-gradient(90deg, transparent 0px, transparent 18px, rgba(0,0,0,0.04) 18px, rgba(0,0,0,0.04) 20px), repeating-linear-gradient(90deg, transparent 0px, transparent 47px, rgba(0,0,0,0.03) 47px, rgba(0,0,0,0.03) 50px), linear-gradient(180deg, rgba(0,0,0,0.15) 0%, transparent 30%, transparent 70%, rgba(0,0,0,0.2) 100%)",
    });
    container.appendChild(bgTexture);

    // Content
    const content = document.createElement("div");
    Object.assign(content.style, {
      position: "relative", zIndex: "2", display: "flex", flexDirection: "column",
      alignItems: "center", width: "100%", maxWidth: "1200px",
      padding: "48px 24px 64px", boxSizing: "border-box", gap: "40px",
    });

    // 1. Winner banner
    const banner = document.createElement("div");
    Object.assign(banner.style, { display: "flex", flexDirection: "column", alignItems: "center", gap: "8px" });

    const bannerTitle = document.createElement("div");
    bannerTitle.textContent = isReformers ? "REFORMERS WIN" : "EXPLOITERS WIN";
    Object.assign(bannerTitle.style, {
      fontSize: "72px", fontWeight: "400", color: accentBorder,
      letterSpacing: "6px", textAlign: "center",
      textShadow: "4px 4px 0 rgba(0,0,0,0.5)", lineHeight: "1",
    });
    banner.appendChild(bannerTitle);

    const bannerSub = document.createElement("div");
    bannerSub.textContent = isReformers ? "Sustainable policies prevailed." : "Exploitative policies dominated.";
    Object.assign(bannerSub.style, { fontSize: "28px", color: "#d4cfc5", letterSpacing: "2px", textAlign: "center" });
    banner.appendChild(bannerSub);

    const line = document.createElement("div");
    Object.assign(line.style, {
      width: "300px", height: "4px", marginTop: "8px",
      background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
    });
    banner.appendChild(line);
    content.appendChild(banner);

    // 2. Player cards
    const playersSection = document.createElement("div");
    Object.assign(playersSection.style, { display: "flex", flexDirection: "column", alignItems: "center", gap: "16px", width: "100%" });

    const playersSectionTitle = document.createElement("div");
    playersSectionTitle.textContent = "ROLES REVEALED";
    Object.assign(playersSectionTitle.style, { fontSize: "36px", color: "#d4a843", letterSpacing: "3px", textAlign: "center" });
    playersSection.appendChild(playersSectionTitle);

    const cardsRow = document.createElement("div");
    Object.assign(cardsRow.style, { display: "flex", gap: "20px", justifyContent: "center", flexWrap: "wrap" });
    this.players.forEach((player) => cardsRow.appendChild(this.buildPlayerCard(player)));
    playersSection.appendChild(cardsRow);
    content.appendChild(playersSection);

    // 3. Enacted policies
    const policiesSection = document.createElement("div");
    Object.assign(policiesSection.style, { display: "flex", flexDirection: "column", alignItems: "center", gap: "16px", width: "100%" });

    const policiesSectionTitle = document.createElement("div");
    policiesSectionTitle.textContent = "ENACTED POLICIES";
    Object.assign(policiesSectionTitle.style, { fontSize: "36px", color: "#d4a843", letterSpacing: "3px", textAlign: "center" });
    policiesSection.appendChild(policiesSectionTitle);

    const holdersRow = document.createElement("div");
    Object.assign(holdersRow.style, { display: "flex", gap: "32px", justifyContent: "center", flexWrap: "wrap", width: "100%" });
    holdersRow.appendChild(this.buildPolicyHolder("#66785a", "#809671", "SUSTAINABLE", this.enactedSustainable, 5));
    holdersRow.appendChild(this.buildPolicyHolder("#842929", "#bc6262", "EXPLOITATIVE", this.enactedExploitative, 3));
    policiesSection.appendChild(holdersRow);
    content.appendChild(policiesSection);

    // 4. Back to menu
    const btnRow = document.createElement("div");
    Object.assign(btnRow.style, { display: "flex", justifyContent: "center", marginTop: "8px" });

    const menuBtn = document.createElement("button");
    menuBtn.textContent = "BACK TO MAIN MENU";
    Object.assign(menuBtn.style, {
      fontFamily: '"Jersey 20", sans-serif', fontSize: "36px", fontWeight: "400",
      letterSpacing: "3px", color: "#f0ebe3", background: "#7a6a52",
      border: "4px solid #bfa76a", padding: "16px 56px",
      cursor: "pointer", boxShadow: "4px 4px 0 #3a3228", transition: "none", imageRendering: "pixelated",
    });
    menuBtn.addEventListener("mousedown", () => { menuBtn.style.transform = "translateX(4px) translateY(4px)"; menuBtn.style.boxShadow = "0 0 0 #3a3228"; });
    menuBtn.addEventListener("mouseup", () => { menuBtn.style.transform = "translateX(0) translateY(0)"; menuBtn.style.boxShadow = "4px 4px 0 #3a3228"; });
    menuBtn.addEventListener("mouseleave", () => { menuBtn.style.transform = "translateX(0) translateY(0)"; menuBtn.style.boxShadow = "4px 4px 0 #3a3228"; menuBtn.style.filter = "none"; });
    menuBtn.addEventListener("mouseenter", () => { menuBtn.style.filter = "brightness(1.12)"; });
    menuBtn.addEventListener("click", () => { this.cleanup(); this.scene.start("MenuScene"); });
    btnRow.appendChild(menuBtn);
    content.appendChild(btnRow);

    container.appendChild(content);
    parent.appendChild(container);
    this.containerEl = container;

    // Styles
    const style = document.createElement("style");
    style.textContent = `
      #game-over-scene * { image-rendering: pixelated; image-rendering: -moz-crisp-edges; image-rendering: crisp-edges; }
      #game-over-scene button:hover { filter: brightness(1.12); }
      @keyframes gameover-fade-in { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
      #game-over-scene .go-player-card { animation: gameover-fade-in 0.5s ease-out both; }
      #game-over-scene .go-holder { animation: gameover-fade-in 0.6s ease-out both; animation-delay: 0.3s; }
      #game-over-scene .go-slot-filled:hover { outline: 3px solid #d4a843; outline-offset: -3px; filter: brightness(1.15); }
    `;
    document.head.appendChild(style);
    this.injectedStyleEl = style;
  }

  // ─── PLAYER CARD ──────────────────────────────────────────────
  // Matches the HUD's buildPlayerCard sizing: 150×225, flex-end,
  // paddingBottom 15px, with border adding to outer box.

  private buildPlayerCard(player: PlayerInfo): HTMLDivElement {
    const isExploiter = player.role === "exploiter";
    const roleColor = isExploiter ? "#842929" : "#66785a";

    const card = document.createElement("div");
    card.classList.add("go-player-card");
    Object.assign(card.style, {
      width: "150px",
      height: "225px",
      backgroundImage: `url("${ASSETS.player_basecard}")`,
      backgroundSize: "cover",
      backgroundPosition: "center",
      backgroundRepeat: "no-repeat",
      border: `4px solid ${roleColor}`,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "flex-end",
      paddingBottom: "11px",
      boxSizing: "border-box",
      overflow: "hidden",
      boxShadow: `0 0 12px ${roleColor}66, 4px 4px 0 rgba(0,0,0,0.4)`,
      position: "relative",
    });
    card.style.animationDelay = `${this.players.indexOf(player) * 0.1}s`;

    // Character sprite — same sizing as HUD (84×112)
    if (player.characterId > 0) {
      const charImg = document.createElement("img");
      charImg.src = `assets/character${player.characterId}.png`;
      charImg.alt = player.name;
      charImg.draggable = false;
      Object.assign(charImg.style, {
        width: "84px",
        height: "112px",
        objectFit: "contain",
        imageRendering: "pixelated",
        pointerEvents: "none",
        marginBottom: "1px",
      });
      card.appendChild(charImg);
    }

    // Name
    const name = document.createElement("div");
    name.textContent = player.name;
    Object.assign(name.style, {
      fontSize: "30px",
      color: "#514b3f",
      textAlign: "center",
      lineHeight: "1.1",
    });
    card.appendChild(name);

    // Role
    const role = document.createElement("div");
    role.textContent = player.role.toUpperCase();
    Object.assign(role.style, {
      fontSize: "26px",
      color: roleColor,
      letterSpacing: "1px",
      marginTop: "5px",
      minHeight: "25px",
      textAlign: "center",
    });
    card.appendChild(role);

    return card;
  }

  // ─── POLICY HOLDER ────────────────────────────────────────────

  private buildPolicyHolder(bgColor: string, borderColor: string, titleText: string, policies: PolicyInfo[], totalSlots: number): HTMLDivElement {
    const holder = document.createElement("div");
    holder.classList.add("go-holder");
    Object.assign(holder.style, {
      width: "480px", maxWidth: "90vw", background: bgColor,
      border: `4px solid ${borderColor}`,
      boxShadow: "4px 4px 0 rgba(0,0,0,0.5)", display: "flex",
      flexDirection: "column", alignItems: "center", justifyContent: "flex-start",
      boxSizing: "border-box", padding: "16px 16px 20px", gap: "14px",
    });

    const title = document.createElement("div");
    title.textContent = titleText;
    Object.assign(title.style, { fontSize: "32px", color: "#f0ebe3", letterSpacing: "3px", textAlign: "center" });
    holder.appendChild(title);

    const slotsRow = document.createElement("div");
    Object.assign(slotsRow.style, { display: "flex", alignItems: "flex-start", justifyContent: "center", gap: "10px", flexWrap: "wrap" });

    const slotW = 100;
    const slotH = 132;

    for (let i = 0; i < totalSlots; i++) {
      const isFilled = i < policies.length;

      const col = document.createElement("div");
      Object.assign(col.style, { display: "flex", flexDirection: "column", alignItems: "center", gap: "6px" });

      const slot = document.createElement("div");
      Object.assign(slot.style, {
        width: `${slotW}px`, height: `${slotH}px`,
        border: `4px solid ${borderColor}`, boxSizing: "border-box",
        position: "relative", overflow: "hidden",
      });

      if (isFilled) {
        slot.classList.add("go-slot-filled");
        Object.assign(slot.style, {
          backgroundImage: `url("${ASSETS.policy_folder}")`, backgroundSize: "cover",
          backgroundPosition: "center", backgroundRepeat: "no-repeat",
          imageRendering: "pixelated", cursor: "pointer",
        });

        const policy = policies[i];
        slot.addEventListener("click", () => {
          this.openPolicyDesc(policy.title, policy.description);
        });
      } else {
        Object.assign(slot.style, { background: "rgba(0, 0, 0, 0.25)" });
      }

      col.appendChild(slot);

      // Context "?" button for filled slots
      if (isFilled) {
        const policy = policies[i];
        const ctxBtn = document.createElement("button");
        ctxBtn.textContent = "?";
        Object.assign(ctxBtn.style, {
          width: "28px", height: "28px", background: "#4a6fa5",
          border: "3px solid #6b8fc4", color: "#e8e4dc",
          fontSize: "18px", fontFamily: '"Jersey 20", sans-serif', fontWeight: "400",
          cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
          padding: "0", lineHeight: "1", boxShadow: "2px 2px 0 rgba(0,0,0,0.3)", imageRendering: "pixelated",
        });
        ctxBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          this.openContext(policy.title, policy.hover || "");
        });
        col.appendChild(ctxBtn);
      }

      slotsRow.appendChild(col);
    }

    holder.appendChild(slotsRow);
    return holder;
  }

  // ─── CLEANUP ──────────────────────────────────────────────────

  private cleanup() {
    if (this.scene.isActive("PolicyDescScene")) this.scene.stop("PolicyDescScene");
    if (this.scene.isActive("ContextScene")) this.scene.stop("ContextScene");

    if (this.containerEl) { this.containerEl.remove(); this.containerEl = undefined; }
    if (this.injectedStyleEl) { this.injectedStyleEl.remove(); this.injectedStyleEl = undefined; }
    if (this.game.canvas) { this.game.canvas.style.display = "block"; }
  }
}