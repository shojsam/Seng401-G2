/**
 * scenes/BoardGameScene.ts — Main game scene (orchestrator).
 *
 * Delegates to:
 *   game/GameState.ts            — shared state
 *   game/HudBuilder.ts           — HUD + phase bar
 *   game/PolicyHolderBuilder.ts  — policy holder panels
 *   game/DrawPileBuilder.ts      — draw pile display
 *   game/OverlayManager.ts       — overlay event wiring
 *   game/GameSocketHandler.ts    — WebSocket + message handlers
 */
import Phaser from "phaser";
import { createGameSocket, getLobbyPlayers, leaveLobby } from "../src/api";
import { GameState } from "../game/GameState";
import { createHUD, updatePhaseBar, TOTAL_HUD } from "../game/HUdBuilder";
import { createPolicyHolders } from "../game/PolicyHolderBuilder";
import { createDrawPile } from "../game/DrawPileBuilder";
import { setupOverlayListeners, hideAllOverlays } from "../game/OverlayManager";
import { connectWebSocket, syncLobbyState, type SocketUICallbacks } from "../game/GameSocketHandler";

const ASSETS = {
  board_bg: "assets/board_bg.png",
  player_basecard: "assets/player_basecard.png",
};

const BASE_WIDTH = 1920;

export class BoardGameScene extends Phaser.Scene {
  private state = new GameState();
  private socket?: WebSocket;
  private resizeHandler?: () => void;

  // DOM element references
  private hudEl?: HTMLDivElement;
  private holdersEl?: HTMLDivElement;
  private drawPileEl?: HTMLDivElement;
  private phaseBarEl?: HTMLDivElement;

  // Phaser objects
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
    const data = (this.scene.settings.data as { username?: string; lobbyCode?: string } | undefined) ?? {};
    this.state.username = (data.username ?? "").trim();
    this.state.lobbyCode = (data.lobbyCode ?? "").trim().toUpperCase();

    document.body.style.overflowX = "hidden";
    document.body.style.overflowY = "auto";
    document.documentElement.style.overflowX = "hidden";
    document.documentElement.style.overflowY = "auto";

    this.state.players = this.state.username ? [{ name: this.state.username }] : [];

    this.rebuildAll();

    this.resizeHandler = () => this.rebuildAll();
    window.addEventListener("resize", this.resizeHandler);

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);

    // Launch overlay scenes
    this.launchOverlayScenes();

    // Wire overlay events → WebSocket
    setupOverlayListeners(this, this.state, (type, data) => this.sendMessage(type, data));

    // After overlay listeners are set up, trigger HUD rebuild so character selection works
    const charScene = this.scene.get("CharacterSelectionScene");
    if (charScene) {
      charScene.events.on("character-selected", () => this.rebuildHUD());
    }

    // Network
    void syncLobbyState(this.state, this.uiCallbacks());
    this.socket = connectWebSocket(this, this.state, (t, d) => this.sendMessage(t, d), this.uiCallbacks());

    this.socket.addEventListener("open", () => {});
    this.socket.addEventListener("close", () => {});
    this.socket.addEventListener("error", () => {});

    // Auto-show character selection
    this.time.delayedCall(500, () => {
      if (this.state.myCharacterId === 0) {
        const cs = this.scene.get("CharacterSelectionScene") as
          { show: (d: { username: string }) => void } | undefined;
        if (cs) cs.show({ username: this.state.username });
      }
    });
  }

  // ─── UI CALLBACKS (bridge for GameSocketHandler) ──────────────

  private uiCallbacks(): SocketUICallbacks {
    return {
      rebuildHUD: () => this.rebuildHUD(),
      rebuildPolicyHolders: () => this.rebuildPolicyHolders(),
      rebuildDrawPile: () => this.rebuildDrawPile(),
      updatePlayers: (names: string[]) => {
        // Preserve existing characterId data when updating player list
        const existing = new Map(this.state.players.map((p) => [p.name, p]));
        this.state.players = names.map((name) => existing.get(name) ?? { name });
        this.rebuildHUD();
      },
      getPhaseBarEl: () => this.phaseBarEl,
    };
  }

  // ─── SEND MESSAGE ─────────────────────────────────────────────

  private sendMessage(type: string, data: Record<string, unknown> = {}) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, data }));
    }
  }

  // ─── REBUILD HELPERS ──────────────────────────────────────────

  private rebuildAll() {
    this.layoutScene();
    this.rebuildHUD();
    this.rebuildPolicyHolders();
    this.rebuildDrawPile();
  }

  private rebuildHUD() {
    const result = createHUD(this.state, BASE_WIDTH, (id, z) => this.createScaledWrapper(id, z));
    this.hudEl = result.hudWrapper;
    this.phaseBarEl = result.phaseBarEl;
  }

  private rebuildPolicyHolders() {
    this.holdersEl = createPolicyHolders(
      this.state,
      () => this.getBgAspect(),
      (id, z) => this.createScaledWrapper(id, z),
      (policy) => {
        const policyDescScene = this.scene.get("PolicyDescScene") as
          { show: (d: { title: string; description: string }) => void } | undefined;
        if (policyDescScene) {
          policyDescScene.show({ title: policy.title, description: policy.description });
        }
      },
    );
  }

  private rebuildDrawPile() {
    this.drawPileEl = createDrawPile(
      this.state.policyDrawCount,
      () => this.getBgAspect(),
      (id, z) => this.createScaledWrapper(id, z),
    );
  }

  // ─── OVERLAY SCENE LAUNCHES ───────────────────────────────────

  private launchOverlayScenes() {
    if (!this.scene.isActive("RoleScene"))
      this.scene.launch("RoleScene", { role: "reformer" });
    if (!this.scene.isActive("VotingScene"))
      this.scene.launch("VotingScene", { nominatorName: "", nomineeName: "" });
    if (!this.scene.isActive("NominationScene"))
      this.scene.launch("NominationScene", { players: [] });
    if (!this.scene.isActive("CharacterSelectionScene"))
      this.scene.launch("CharacterSelectionScene", { username: this.state.username });
    if (!this.scene.isActive("PolicyDescScene"))
      this.scene.launch("PolicyDescScene", { title: "", description: "" });
    if (!this.scene.isActive("DiscardPolicyScene"))
      this.scene.launch("DiscardPolicyScene");
    if (!this.scene.isActive("PolicyEnactScene"))
      this.scene.launch("PolicyEnactScene");
  }

  // ─── LAYOUT (Phaser canvas) ───────────────────────────────────

  private getScale(): number {
    return window.innerWidth / BASE_WIDTH;
  }

  private getBgAspect(): number {
    const bgTex = this.textures.get("board_bg").getSourceImage();
    return bgTex.height / bgTex.width;
  }

  private createScaledWrapper(id: string, zIndex: string): { wrapper: HTMLDivElement; inner: HTMLDivElement } {
    const s = this.getScale();
    const canvasH = this.game.canvas.style.height || `${window.innerHeight}px`;

    const wrapper = document.createElement("div");
    wrapper.id = id;
    Object.assign(wrapper.style, {
      position: "absolute", top: "0", left: "0",
      width: `${window.innerWidth}px`, height: canvasH,
      overflow: "hidden", zIndex, pointerEvents: "none",
    });

    const inner = document.createElement("div");
    Object.assign(inner.style, {
      position: "absolute", top: "0", left: "0",
      width: `${BASE_WIDTH}px`,
      transformOrigin: "top left",
      transform: `scale(${s})`,
    });

    wrapper.appendChild(inner);
    return { wrapper, inner };
  }

  private layoutScene() {
    const s = this.getScale();
    const baseBgH = BASE_WIDTH * this.getBgAspect();
    const totalBaseH = TOTAL_HUD + baseBgH;
    const totalCssH = Math.max(totalBaseH * s, window.innerHeight);

    this.scale.resize(BASE_WIDTH, totalBaseH);

    const canvas = this.game.canvas;
    canvas.style.width = `${window.innerWidth}px`;
    canvas.style.height = `${totalCssH}px`;
    canvas.style.pointerEvents = "none"; // Let DOM elements receive clicks

    const container = document.getElementById("game-container");
    if (container) {
      container.style.width = `${window.innerWidth}px`;
      container.style.height = `${totalCssH}px`;
    }

    if (this.bgImage) { this.bgImage.destroy(); this.bgImage = undefined; }
    if (this.dimOverlay) { this.dimOverlay.destroy(); this.dimOverlay = undefined; }
    if (this.hudBgFill) { this.hudBgFill.destroy(); this.hudBgFill = undefined; }

    this.bgImage = this.add.image(BASE_WIDTH / 2, TOTAL_HUD + baseBgH / 2, "board_bg");
    this.bgImage.setDisplaySize(BASE_WIDTH, baseBgH);
    this.bgImage.setDepth(0);

    this.dimOverlay = this.add.rectangle(
      BASE_WIDTH / 2, TOTAL_HUD + baseBgH / 2,
      BASE_WIDTH, baseBgH, 0x353b42, 0.8,
    );
    this.dimOverlay.setDepth(1);

    this.hudBgFill = this.add.rectangle(BASE_WIDTH / 2, TOTAL_HUD / 2, BASE_WIDTH, TOTAL_HUD, 0x0d1b2a, 1);
    this.hudBgFill.setDepth(0);
  }

  // ─── PUBLIC API ───────────────────────────────────────────────

  public addSustainablePolicy() {
    this.state.sustainableCount = Math.min(this.state.sustainableCount + 1, 5);
    this.rebuildPolicyHolders();
  }

  public addExploitativePolicy() {
    this.state.exploitativeCount = Math.min(this.state.exploitativeCount + 1, 3);
    this.rebuildPolicyHolders();
  }

  // ─── CLEANUP ──────────────────────────────────────────────────

  private cleanup() {
    if (this.socket) { this.socket.close(); this.socket = undefined; }
    if (this.state.username) {
      void leaveLobby(this.state.username, this.state.lobbyCode).catch(() => undefined);
    }
    this.hudEl?.remove();
    this.holdersEl?.remove();
    this.drawPileEl?.remove();
    this.hudEl = this.holdersEl = this.drawPileEl = undefined;

    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
      this.resizeHandler = undefined;
    }

    const overlays = [
      "RoleScene", "VotingScene", "NominationScene",
      "CharacterSelectionScene", "PolicyDescScene",
      "DiscardPolicyScene", "PolicyEnactScene",
    ];
    for (const name of overlays) {
      if (this.scene.isActive(name)) this.scene.stop(name);
    }
  }
}
