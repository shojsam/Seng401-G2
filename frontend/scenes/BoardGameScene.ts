import Phaser from "phaser";
import { createGameSocket, getLobbyPlayers, leaveLobby } from "../src/api";

const ASSETS = {
  board_bg: "assets/board_bg.png",
  player_basecard: "assets/player_basecard.png",
  policy_folder: "assets/policy_folder1.png",
};

const HUD_HEIGHT = 250;
const BORDER_HEIGHT = 5;
const TOTAL_HUD = HUD_HEIGHT + BORDER_HEIGHT;

/**
 * Base width used for all DOM element sizing.
 * This is the reference resolution — DOM elements are built at this width
 * and then CSS-scaled to match the actual canvas, so browser zoom
 * never changes their relative proportions.
 */
const BASE_WIDTH = 1920;

interface PlayerData {
  name: string;
  role?: string;
  isActive?: boolean;
  isEliminated?: boolean;
}

type BoardSceneData = {
  username?: string;
  lobbyCode?: string;
};

type SocketMessage = {
  type?: string;
  data?: Record<string, unknown>;
};

export class BoardGameScene extends Phaser.Scene {
  private players: PlayerData[] = [];
  private hudEl?: HTMLDivElement;
  private statusEl?: HTMLDivElement;
  private readyPanelEl?: HTMLDivElement;
  private holdersEl?: HTMLDivElement;
  private drawPileEl?: HTMLDivElement;
  private username = "";
  private lobbyCode = "MAIN";
  private socket?: WebSocket;
  private canStart = false;
  private gameStarted = false;
  private readyPlayers = new Set<string>();

  private sustainableCount = 0;
  private exploitativeCount = 0;
  private policyDrawCount = 20;
  private resizeHandler?: () => void;

  // Tracked Phaser objects (so layoutScene can clean them up properly)
  private bgImage?: Phaser.GameObjects.Image;
  private dimOverlay?: Phaser.GameObjects.Rectangle;
  private hudBgFill?: Phaser.GameObjects.Rectangle;

  constructor() {
    super({ key: "BoardGameScene" });
  }

  preload() {
    this.load.image("board_bg", ASSETS.board_bg);
    this.load.image("player_basecard", ASSETS.player_basecard);
  }

  create() {
    const data = (this.scene.settings.data as BoardSceneData | undefined) ?? {};
    this.username = (data.username ?? "").trim();
    this.lobbyCode = (data.lobbyCode ?? "").trim().toUpperCase();

    document.body.style.overflowX = "hidden";
    document.body.style.overflowY = "auto";
    document.documentElement.style.overflowX = "hidden";
    document.documentElement.style.overflowY = "auto";

    this.players = this.username ? [{ name: this.username }] : [];

    this.layoutScene();
    this.createHUD();
    this.createPolicyHolders();
    this.createDrawPile();

    this.resizeHandler = () => {
      this.layoutScene();
      this.createHUD();
      this.createPolicyHolders();
      this.createDrawPile();
    };
    window.addEventListener("resize", this.resizeHandler);

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);

    if (!this.scene.isActive("RoleScene")) {
      this.scene.launch("RoleScene", { role: "reformer" });
    }

    if (!this.scene.isActive("VotingScene")) {
      this.scene.launch("VotingScene", {
        nominatorName: "Player 1",
        nomineeName: "Player 2",
      });
    }

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

    if (!this.scene.isActive("CharacterSelectionScene")) {
      this.scene.launch("CharacterSelectionScene", {
        username: this.username,
      });
    }

    if (!this.scene.isActive("PolicyDescScene")) {
      this.scene.launch("PolicyDescScene", {
        title: "CARBON TAX",
        description:
          "Impose a tax on carbon emissions from major industrial polluters. Revenue is redirected toward renewable energy infrastructure and green subsidies.",
      });
    }

    if (!this.scene.isActive("DiscardPolicyScene")) {
      this.scene.launch("DiscardPolicyScene");
    }

    if (!this.scene.isActive("PolicyEnactScene")) {
      this.scene.launch("PolicyEnactScene");
    }

    void this.syncLobbyState();
    this.connectWebSocket();
  }

  // ─── HELPERS ──────────────────────────────────────────────────────

  /** Returns the CSS scale factor to map BASE_WIDTH onto the actual viewport */
  private getScale(): number {
    return window.innerWidth / BASE_WIDTH;
  }

  /** Background aspect ratio */
  private getBgAspect(): number {
    const bgTex = this.textures.get("board_bg").getSourceImage();
    return bgTex.height / bgTex.width;
  }

  /** Background display height at BASE_WIDTH */
  private getBaseBgH(): number {
    return BASE_WIDTH * this.getBgAspect();
  }

  /**
   * Creates a clipping wrapper div that is sized to the actual viewport
   * but contains a child laid out at BASE_WIDTH and CSS-scaled down.
   * This prevents the unscaled 1920px element from causing scrollbars.
   */
  private createScaledWrapper(id: string, zIndex: string): { wrapper: HTMLDivElement; inner: HTMLDivElement } {
    const s = this.getScale();
    const canvasH = this.game.canvas.style.height || `${window.innerHeight}px`;

    const wrapper = document.createElement("div");
    wrapper.id = id;
    Object.assign(wrapper.style, {
      position: "absolute",
      top: "0",
      left: "0",
      width: `${window.innerWidth}px`,
      height: canvasH,
      overflow: "hidden",
      zIndex,
      pointerEvents: "none",
    });

    const inner = document.createElement("div");
    Object.assign(inner.style, {
      position: "absolute",
      top: "0",
      left: "0",
      width: `${BASE_WIDTH}px`,
      transformOrigin: "top left",
      transform: `scale(${s})`,
    });

    wrapper.appendChild(inner);
    return { wrapper, inner };
  }

  // ─── LAYOUT (canvas-based content) ────────────────────────────────

  private layoutScene() {
    const s = this.getScale();
    const baseBgH = this.getBaseBgH();
    const totalBaseH = TOTAL_HUD + baseBgH;
    const totalCssH = Math.max(totalBaseH * s, window.innerHeight);

    // Phaser world is always laid out at BASE_WIDTH
    this.scale.resize(BASE_WIDTH, totalBaseH);

    // Force canvas to fill viewport width; height scales proportionally
    const canvas = this.game.canvas;
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${totalCssH}px`;

    // Size the game container to match so scrolling works
    const container = document.getElementById("game-container");
    if (container) {
      container.style.width = `${window.innerWidth}px`;
      container.style.height = `${totalCssH}px`;
    }

    // Destroy previous objects before recreating
    if (this.bgImage) { this.bgImage.destroy(); this.bgImage = undefined; }
    if (this.dimOverlay) { this.dimOverlay.destroy(); this.dimOverlay = undefined; }
    if (this.hudBgFill) { this.hudBgFill.destroy(); this.hudBgFill = undefined; }

    this.bgImage = this.add.image(BASE_WIDTH / 2, TOTAL_HUD + baseBgH / 2, "board_bg");
    this.bgImage.setDisplaySize(BASE_WIDTH, baseBgH);
    this.bgImage.setDepth(0);

    this.dimOverlay = this.add.rectangle(
      BASE_WIDTH / 2,
      TOTAL_HUD + baseBgH / 2,
      BASE_WIDTH,
      baseBgH,
      0x353b42,
      0.8
    );
    this.dimOverlay.setDepth(1);

    this.hudBgFill = this.add.rectangle(BASE_WIDTH / 2, TOTAL_HUD / 2, BASE_WIDTH, TOTAL_HUD, 0x0d1b2a, 1);
    this.hudBgFill.setDepth(0);
  }

  // ─── DOM-BASED POLICY HOLDERS ─────────────────────────────────────

  private createPolicyHolders() {
    const existing = document.getElementById("policy-holders-wrapper");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;
    const s = this.getScale();
    const baseBgH = this.getBaseBgH();

    const holderW = BASE_WIDTH * 0.42;
    const holderH = holderW * 0.65;
    const holderY = TOTAL_HUD + baseBgH * 0.3 - holderH / 2;

    const { wrapper, inner } = this.createScaledWrapper("policy-holders-wrapper", "10");

    const container = document.createElement("div");
    container.id = "policy-holders";
    Object.assign(container.style, {
      width: `${BASE_WIDTH}px`,
      display: "flex",
      justifyContent: "center",
      gap: `${BASE_WIDTH * 0.06}px`,
      paddingTop: `${holderY}px`,
      pointerEvents: "none",
      fontFamily: '"Jersey 20", sans-serif',
    });

    container.appendChild(
      this.buildHolder(
        holderW,
        holderH,
        "#66785a",
        "#809671",
        "SUSTAINABLE",
        "REFORMERS MUST PASS 5\nSUSTAINABLE POLICIES TO WIN",
        this.sustainableCount,
        5
      )
    );

    container.appendChild(
      this.buildHolder(
        holderW,
        holderH,
        "#842929",
        "#bc6262",
        "EXPLOITATIVE",
        "EXPLOITERS MUST PASS 3\nEXPLOITATIVE POLICIES TO WIN",
        this.exploitativeCount,
        3
      )
    );

    inner.appendChild(container);
    parent.appendChild(wrapper);
    this.holdersEl = wrapper;
  }

  private buildHolder(
    w: number,
    h: number,
    bgColor: string,
    borderColor: string,
    titleText: string,
    descText: string,
    filled: number,
    total: number
  ): HTMLDivElement {
    const holder = document.createElement("div");
    Object.assign(holder.style, {
      width: `${w}px`,
      height: `${h}px`,
      background: bgColor,
      border: `4px solid ${borderColor}`,
      borderRadius: "4px",
      boxShadow: "4px 4px 0 rgba(0,0,0,0.5)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "space-between",
      boxSizing: "border-box",
      padding: "16px",
    });

    const title = document.createElement("div");
    title.textContent = titleText;
    Object.assign(title.style, {
      fontSize: `${Math.max(32, Math.floor(w * 0.08))}px`,
      color: "#f0ebe3",
      letterSpacing: "3px",
      textAlign: "center",
    });
    holder.appendChild(title);

    // ── Policy card slots (56×74 aspect ratio) ──────────────────────
    const slotsRow = document.createElement("div");
    Object.assign(slotsRow.style, {
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "10px",
    });

    const scale = 2.25;
    const slotW = Math.floor(56 * scale);
    const slotH = Math.floor(74 * scale);

    for (let i = 0; i < total; i++) {
      const slot = document.createElement("div");
      Object.assign(slot.style, {
        width: `${slotW}px`,
        height: `${slotH}px`,
        background: "rgba(0, 0, 0, 0.25)",
        border: `4px solid ${borderColor}`,
        boxSizing: "border-box",
      });
      slotsRow.appendChild(slot);
    }

    holder.appendChild(slotsRow);

    const desc = document.createElement("div");
    desc.textContent = descText;
    Object.assign(desc.style, {
      fontSize: `${Math.max(18, Math.floor(w * 0.045))}px`,
      color: "#d4cfc5",
      textAlign: "center",
      lineHeight: "1.3",
      whiteSpace: "pre-line",
    });
    holder.appendChild(desc);

    return holder;
  }

  // ─── DRAW PILE ────────────────────────────────────────────────────

  private createDrawPile() {
    const existing = document.getElementById("draw-pile-wrapper");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;
    const baseBgH = this.getBaseBgH();

    const holderW = BASE_WIDTH * 0.42;
    const holderH = holderW * 0.65;
    const holderY = TOTAL_HUD + baseBgH * 0.35 - holderH / 2;

    // Position below the sustainable holder (left side)
    const pileTop = holderY + holderH + 70;
    const pileCenterX = BASE_WIDTH * 0.25;

    // The table inside is (56*2.25 + 60) = 186px wide
    const pileW = Math.floor(56 * 2.25) + 60;

    const { wrapper, inner } = this.createScaledWrapper("draw-pile-wrapper", "10");

    const pile = this.buildDrawPile(this.policyDrawCount);
    pile.id = "draw-pile";
    Object.assign(pile.style, {
      position: "absolute",
      top: `${pileTop}px`,
      left: `${pileCenterX - pileW / 2}px`,
      pointerEvents: "none",
    });

    inner.appendChild(pile);
    parent.appendChild(wrapper);
    this.drawPileEl = wrapper;
  }

  private buildDrawPile(count: number): HTMLDivElement {
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

    // ── Table surface ───────────────────────────────────────────────
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

    // ── Stacked cards ───────────────────────────────────────────────
    const stackH = maxVisibleCards * stackOffset;
    const stackContainer = document.createElement("div");
    Object.assign(stackContainer.style, {
      position: "absolute",
      left: "50%",
      transform: "translateX(-50%)",
      bottom: `${bottomPad + labelH + labelGap}px`,
      width: `${cardW}px`,
      height: `${cardH + stackH}px`,
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
        backgroundImage: `url("${ASSETS.policy_folder}")`,
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

    // ── Count label ─────────────────────────────────────────────────
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

  // ─── HUD ──────────────────────────────────────────────────────────

  private createHUD() {
    const existing = document.getElementById("board-hud-wrapper");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;
    const { wrapper, inner } = this.createScaledWrapper("board-hud-wrapper", "100");
    wrapper.style.pointerEvents = "auto";

    const hud = document.createElement("div");
    hud.id = "board-hud";
    Object.assign(hud.style, {
      width: `${BASE_WIDTH}px`,
      height: `${HUD_HEIGHT}px`,
      background: "#5c3d2e",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "20px",
      borderBottom: `${BORDER_HEIGHT}px solid #d4a843`,
      boxSizing: "content-box",
      fontFamily: '"Jersey 20", sans-serif',
      flexWrap: "wrap",
      padding: "12px",
      boxShadow: "0px 8px 0 rgba(0,0,0,0.5)",
      position: "relative",
    });

    // ── Player cards ────────────────────────────────────────────────
    this.players.forEach((player) => {
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

    // ── Status info (top-right of HUD) ──────────────────────────────
    const statusInfo = document.createElement("div");
    statusInfo.id = "board-status";
    Object.assign(statusInfo.style, {
      position: "absolute",
      top: "10px",
      right: "14px",
      fontFamily: '"Jersey 20", sans-serif',
      fontSize: "20px",
      color: "#9e9a92",
      textAlign: "right",
      lineHeight: "1.4",
      pointerEvents: "none",
    });
    hud.appendChild(statusInfo);
    this.statusEl = statusInfo;
    this.setStatus("Connecting...");

    const readyPanel = document.createElement("div");
    readyPanel.id = "board-ready-panel";
    Object.assign(readyPanel.style, {
      position: "absolute",
      top: "10px",
      left: "14px",
      display: "flex",
      flexDirection: "column",
      alignItems: "flex-start",
      gap: "8px",
      fontFamily: '"Jersey 20", sans-serif',
      color: "#e8e4dc",
      maxWidth: "360px",
    });
    hud.appendChild(readyPanel);
    this.readyPanelEl = readyPanel;
    this.renderReadyPanel();

    inner.appendChild(hud);
    parent.appendChild(wrapper);
    this.hudEl = wrapper;
  }

  private setStatus(message: string) {
    if (!this.statusEl) return;
    this.statusEl.innerHTML =
      `<span style="color:#e8e4dc">${this.username || "?"}</span>` +
      ` · ` +
      `<span style="color:#d4a843">${this.lobbyCode}</span>` +
      ` · ` +
      `${message}`;
  }

  private renderReadyPanel() {
    if (!this.readyPanelEl) return;

    this.readyPanelEl.innerHTML = "";

    if (this.gameStarted) {
      return;
    }

    const info = document.createElement("div");
    Object.assign(info.style, {
      fontSize: "22px",
      lineHeight: "1.25",
      color: "#f0ebe3",
    });

    const readyCount = this.readyPlayers.size;
    const playerCount = this.players.length;

    if (playerCount < 5) {
      info.textContent = `Waiting for players: ${playerCount}/5 in lobby`;
      this.readyPanelEl.appendChild(info);
      return;
    }

    info.textContent = `Ready check: ${readyCount}/${playerCount} players ready`;
    this.readyPanelEl.appendChild(info);

    const detail = document.createElement("div");
    Object.assign(detail.style, {
      fontSize: "18px",
      lineHeight: "1.2",
      color: "#d4cfc5",
    });
    detail.textContent = this.readyPlayers.has(this.username)
      ? "You are ready. Waiting for the rest of the lobby."
      : "All players must press ready to start the game.";
    this.readyPanelEl.appendChild(detail);

    const button = document.createElement("button");
    const isReady = this.readyPlayers.has(this.username);
    button.textContent = isReady ? "Unready" : "Ready";
    button.disabled = !this.socket || this.socket.readyState !== WebSocket.OPEN;
    Object.assign(button.style, {
      minWidth: "160px",
      height: "52px",
      borderRadius: "4px",
      border: "4px solid #e0b66a",
      background: isReady ? "#6b6355" : "#37935a",
      color: "#f0ebe3",
      fontSize: "28px",
      letterSpacing: "1px",
      cursor: button.disabled ? "default" : "pointer",
      boxShadow: "4px 4px 0 rgba(0,0,0,0.35)",
      fontFamily: '"Jersey 20", sans-serif',
    });
    button.onclick = () => {
      this.sendSocketMessage(isReady ? "unready" : "ready_up");
    };
    this.readyPanelEl.appendChild(button);
  }

  private sendSocketMessage(type: string, data?: Record<string, unknown>) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      this.setStatus("Socket not connected");
      return;
    }

    this.socket.send(JSON.stringify(data ? { type, data } : { type }));
  }

  // ─── NETWORKING ───────────────────────────────────────────────────

  private async syncLobbyState() {
    try {
      const data = await getLobbyPlayers(this.lobbyCode);
      this.updatePlayers(data.players.map((name) => ({ name })));
      this.setStatus(`${data.players.length} players`);
    } catch (error) {
      this.setStatus(
        error instanceof Error ? `Sync failed: ${error.message}` : "Sync failed"
      );
    }
  }

  private connectWebSocket() {
    if (!this.username) {
      this.setStatus("Missing name");
      return;
    }

    this.socket?.close();
    const socket = createGameSocket(this.lobbyCode, this.username);
    this.socket = socket;

    socket.addEventListener("open", () => {
      this.setStatus("Connected");
      this.renderReadyPanel();
    });

    socket.addEventListener("message", (event) => {
      try {
        const message = JSON.parse(event.data) as SocketMessage;

        if (message.type === "lobby_update") {
          const players = Array.isArray(message.data?.players)
            ? (message.data.players as string[])
            : [];
          const readyPlayers = Array.isArray(message.data?.ready_players)
            ? (message.data.ready_players as string[])
            : [];
          this.updatePlayers(players.map((name) => ({ name })));
          this.readyPlayers = new Set(readyPlayers);
          this.canStart = Boolean(message.data?.can_start);
          if (this.canStart && readyPlayers.length === players.length) {
            this.setStatus("All players ready. Starting...");
          } else if (this.canStart) {
            this.setStatus(`${readyPlayers.length}/${players.length} ready`);
          } else {
            this.setStatus(`${players.length} players`);
          }
          this.renderReadyPanel();
          return;
        }

        if (message.type === "game_started") {
          this.gameStarted = true;
          this.readyPlayers.clear();
          this.renderReadyPanel();
          this.setStatus("Game started");
          return;
        }

        if (message.type === "player_disconnected") {
          const disconnectedUser = String(message.data?.username ?? "A player");
          this.readyPlayers.delete(disconnectedUser);
          this.renderReadyPanel();
          this.setStatus(`${disconnectedUser} left`);
          return;
        }

        if (message.type === "game_reset") {
          this.gameStarted = false;
          this.readyPlayers.clear();
          this.renderReadyPanel();
          this.setStatus("Game reset");
          return;
        }

        if (message.type === "phase_change") {
          const phase = String(message.data?.phase ?? "");
          this.gameStarted = phase !== "lobby";
          this.renderReadyPanel();
          this.setStatus(phase.replace(/_/g, " "));
          return;
        }

        if (message.type === "error") {
          const backendMessage = String(message.data?.message ?? "Unknown error");
          this.setStatus(`Error: ${backendMessage}`);
          this.renderReadyPanel();
        }
      } catch {
        this.setStatus("Bad message");
      }
    });

    socket.addEventListener("close", () => {
      if (this.socket === socket) {
        this.setStatus("Disconnected");
        this.renderReadyPanel();
      }
    });

    socket.addEventListener("error", () => {
      this.setStatus("Connection failed");
      this.renderReadyPanel();
    });
  }

  // ─── PUBLIC API ───────────────────────────────────────────────────

  public updatePlayers(players: PlayerData[]) {
    this.players = players;
    this.readyPlayers.forEach((name) => {
      if (!players.some((player) => player.name === name)) {
        this.readyPlayers.delete(name);
      }
    });
    this.createHUD();
  }

  public addSustainablePolicy() {
    this.sustainableCount = Math.min(this.sustainableCount + 1, 5);
    this.createPolicyHolders();
  }

  public addExploitativePolicy() {
    this.exploitativeCount = Math.min(this.exploitativeCount + 1, 3);
    this.createPolicyHolders();
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
    const username = this.username;

    if (this.socket) {
      this.socket.close();
      this.socket = undefined;
    }

    if (username) {
      void leaveLobby(username, this.lobbyCode).catch(() => undefined);
    }

    if (this.hudEl) {
      this.hudEl.remove();
      this.hudEl = undefined;
    }

    if (this.holdersEl) {
      this.holdersEl.remove();
      this.holdersEl = undefined;
    }

    if (this.drawPileEl) {
      this.drawPileEl.remove();
      this.drawPileEl = undefined;
    }

    this.statusEl = undefined;
    this.readyPanelEl = undefined;

    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
      this.resizeHandler = undefined;
    }

    if (this.scene.isActive("RoleScene")) {
      this.scene.stop("RoleScene");
    }

    if (this.scene.isActive("VotingScene")) {
      this.scene.stop("VotingScene");
    }

    if (this.scene.isActive("NominationScene")) {
      this.scene.stop("NominationScene");
    }

    if (this.scene.isActive("CharacterSelectionScene")) {
      this.scene.stop("CharacterSelectionScene");
    }

    if (this.scene.isActive("PolicyDescScene")) {
      this.scene.stop("PolicyDescScene");
    }

    if (this.scene.isActive("DiscardPolicyScene")) {
      this.scene.stop("DiscardPolicyScene");
    }

    if (this.scene.isActive("PolicyEnactScene")) {
      this.scene.stop("PolicyEnactScene");
    }
  }
}
