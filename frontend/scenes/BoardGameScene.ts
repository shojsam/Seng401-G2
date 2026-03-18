import Phaser from "phaser";

/**
 * Asset keys and paths — place images in your public/assets folder:
 *
 *   board_bg.png          → UN courtroom background
 *   card_sustainable.png  → Blue "SUSTAINABLE" card holder (transparent bg)
 *   card_exploitative.png → Red "EXPLOITATIVE" card holder (transparent bg)
 *   player_basecard.png   → Player card background used in the HUD
 */

const ASSETS = {
  board_bg: "assets/board_bg.png",
  card_sustainable: "assets/card_sustainable.png",
  card_exploitative: "assets/card_exploitative.png",
  player_basecard: "assets/player_basecard.png",
};

const HUD_HEIGHT = 250;
const BORDER_HEIGHT = 3;
const TOTAL_HUD = HUD_HEIGHT + BORDER_HEIGHT;

/** Placeholder player data — replace with real game state later */
interface PlayerData {
  name: string;
  role?: string;
  isActive?: boolean;
  isEliminated?: boolean;
}

export class BoardGameScene extends Phaser.Scene {
  private players: PlayerData[] = [];
  private hudEl?: HTMLDivElement;
  private sustainableHolder!: Phaser.GameObjects.Image;
  private exploitativeHolder!: Phaser.GameObjects.Image;

  // Track policy counts for the card holders
  private sustainableCount: number = 0;
  private exploitativeCount: number = 0;

  // Track resize listener so we can clean it up
  private resizeHandler?: () => void;

  constructor() {
    super({ key: "BoardGameScene" });
  }

  // ─── PRELOAD ──────────────────────────────────────────────────────

  preload() {
    this.load.image("board_bg", ASSETS.board_bg);
    this.load.image("card_sustainable", ASSETS.card_sustainable);
    this.load.image("card_exploitative", ASSETS.card_exploitative);
    this.load.image("player_basecard", ASSETS.player_basecard);
  }

  // ─── CREATE ───────────────────────────────────────────────────────

  create() {
    // Enable native browser scrolling (MenuScene uses it too)
    document.body.style.overflowX = "hidden";
    document.body.style.overflowY = "auto";
    document.documentElement.style.overflowX = "hidden";
    document.documentElement.style.overflowY = "auto";

    // ── Placeholder players (replace with lobby data) ─────────────
    this.players = [
      { name: "Player 1" },
      { name: "Player 2" },
      { name: "Player 3" },
      { name: "Player 4" },
      { name: "Player 5" },
      { name: "Player 6" },
    ];

    // ── Layout everything ─────────────────────────────────────────
    this.layoutScene();
    this.createHUD();

    // ── Handle window resize ──────────────────────────────────────
    this.resizeHandler = () => this.layoutScene();
    window.addEventListener("resize", this.resizeHandler);

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);

    // ── Launch the RoleScene overlay in parallel ──────────────────
    if (!this.scene.isActive("RoleScene")) {
      this.scene.launch("RoleScene", { role: "reformer" });
    }

    // ── Launch the VotingScene overlay in parallel ────────────────
    if (!this.scene.isActive("VotingScene")) {
      this.scene.launch("VotingScene", {
        nominatorName: "Player 1",
        nomineeName: "Player 2",
      });
    }

    // ── Launch the NominationScene overlay in parallel ────────────
    if (!this.scene.isActive("NominationScene")) {
      this.scene.launch("NominationScene", {
        players: [
          { name: "Player 2", eligible: true },
          { name: "Player 3", eligible: true },
          { name: "Player 4", eligible: false },
          { name: "Player 5", eligible: true },
          { name: "Player 6", eligible: true },
        ],
      });
    }
  }

  // ─── LAYOUT (canvas-based content) ────────────────────────────────

  private layoutScene() {
    const width = window.innerWidth;

    // Calculate background height from its natural aspect ratio
    const bgTex = this.textures.get("board_bg").getSourceImage();
    const bgAspect = bgTex.height / bgTex.width;
    const bgDisplayH = width * bgAspect;

    // Total canvas height = HUD space + background at natural aspect ratio
    const totalH = Math.max(TOTAL_HUD + bgDisplayH, window.innerHeight);

    // Resize the Phaser game canvas to fit all content
    this.scale.resize(width, totalH);

    // Also explicitly size the canvas element so the page is scrollable
    this.game.canvas.style.width = `${width}px`;
    this.game.canvas.style.height = `${totalH}px`;

    // ── Background ────────────────────────────────────────────────
    const oldBg = this.children.list.find(
      (c) => c instanceof Phaser.GameObjects.Image && c.texture.key === "board_bg"
    );
    if (oldBg) oldBg.destroy();

    const bg = this.add.image(width / 2, TOTAL_HUD + bgDisplayH / 2, "board_bg");
    bg.setDisplaySize(width, bgDisplayH);
    bg.setDepth(0);

    // Dim overlay
    const dimOverlay = this.add.rectangle(width / 2, TOTAL_HUD + bgDisplayH / 2, width, bgDisplayH, 0x353b42, 0.8);
    dimOverlay.setDepth(1);

    // Fill area above background (behind HUD) with solid color
    const oldHudBg = this.children.list.find(
      (c) => c instanceof Phaser.GameObjects.Rectangle && (c as any).name === "hud_bg_fill"
    );
    if (oldHudBg) oldHudBg.destroy();

    const hudBgFill = this.add.rectangle(width / 2, TOTAL_HUD / 2, width, TOTAL_HUD, 0x0d1b2a, 1);
    (hudBgFill as any).name = "hud_bg_fill";
    hudBgFill.setDepth(0);

    // ── Card Holders ──────────────────────────────────────────────
    this.layoutCardHolders(width, bgDisplayH);
  }

  private layoutCardHolders(width: number, bgDisplayH: number) {
    if (this.sustainableHolder) this.sustainableHolder.destroy();
    if (this.exploitativeHolder) this.exploitativeHolder.destroy();

    const holderY = TOTAL_HUD + bgDisplayH * 0.25;
    const leftCenterX = width * 0.25;
    const rightCenterX = width * 0.75;
    const targetW = width * 0.38;

    // ── Sustainable (green) — LEFT ─────────────────────────────────
    this.sustainableHolder = this.add.image(leftCenterX, holderY, "card_sustainable");
    const susTexW = this.sustainableHolder.texture.getSourceImage().width;
    this.sustainableHolder.setScale(targetW / susTexW);
    this.sustainableHolder.setDepth(5);

    // ── Exploitative (red) — RIGHT ────────────────────────────────
    this.exploitativeHolder = this.add.image(rightCenterX, holderY, "card_exploitative");
    const expTexW = this.exploitativeHolder.texture.getSourceImage().width;
    this.exploitativeHolder.setScale(targetW / expTexW);
    this.exploitativeHolder.setDepth(5);
  }

  private createHUD() {
    const existing = document.getElementById("board-hud");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    const hud = document.createElement("div");
    hud.id = "board-hud";
    Object.assign(hud.style, {
      position: "absolute",
      top: "0",
      left: "0",
      width: "100%",
      height: `${HUD_HEIGHT}px`,
      background: "#353b42",
      zIndex: "100",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "20px",
      borderBottom: `${BORDER_HEIGHT}px solid #d4a843`,
      boxSizing: "content-box",
      fontFamily: '"Jersey 20", sans-serif',
    });

    this.players.forEach((player, i) => {
      const card = document.createElement("div");
      Object.assign(card.style, {
        width: "150px",
        height: "225px",
        backgroundImage: `url("${ASSETS.player_basecard}")`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        border: "none",
        borderRadius: "8px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-end",
        paddingBottom: "15px",
        boxSizing: "border-box",
        overflow: "hidden",
      });

      const name = document.createElement("div");
      name.textContent = player.name;
      Object.assign(name.style, {
        fontSize: "30px",
        color: player.isEliminated ? "#666666" : "#514b3f",
        textDecoration: player.isEliminated ? "line-through" : "none",
      });

      const role = document.createElement("div");
      role.textContent = player.role ?? "?";
      Object.assign(role.style, {
        fontSize: "26px",
        color: "#514b3f",
        marginTop: "5px",
      });

      card.appendChild(name);
      card.appendChild(role);
      hud.appendChild(card);
    });

    parent.appendChild(hud);
    this.hudEl = hud;
  }

  // ─── PUBLIC API (for game logic to call) ──────────────────────────

  public updatePlayers(players: PlayerData[]) {
    this.players = players;
    this.createHUD();
  }

  public addSustainablePolicy() {
    this.sustainableCount = Math.min(this.sustainableCount + 1, 5);
  }

  public addExploitativePolicy() {
    this.exploitativeCount = Math.min(this.exploitativeCount + 1, 3);
  }

  public setActivePlayer(index: number) {
    this.players.forEach((p, i) => {
      p.isActive = i === index;
    });
    this.createHUD();
  }

  public eliminatePlayer(index: number) {
    if (this.players[index]) {
      this.players[index].isEliminated = true;
      this.createHUD();
    }
  }

  public revealRole(index: number, role: string) {
    if (this.players[index]) {
      this.players[index].role = role;
      this.createHUD();
    }
  }

  // ─── CLEANUP ──────────────────────────────────────────────────────

  private cleanup() {
    if (this.hudEl) {
      this.hudEl.remove();
      this.hudEl = undefined;
    }
    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
      this.resizeHandler = undefined;
    }
    // Stop the RoleScene overlay when BoardGameScene shuts down
    if (this.scene.isActive("RoleScene")) {
      this.scene.stop("RoleScene");
    }
    // Stop the VotingScene overlay when BoardGameScene shuts down
    if (this.scene.isActive("VotingScene")) {
      this.scene.stop("VotingScene");
    }
    // Stop the NominationScene overlay when BoardGameScene shuts down
    if (this.scene.isActive("NominationScene")) {
      this.scene.stop("NominationScene");
    }
  }
}