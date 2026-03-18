import Phaser from "phaser";
import { createGameSocket, getLobbyPlayers, leaveLobby } from "../src/api";

const ASSETS = {
  board_bg: "assets/board_bg.png",
  card_sustainable: "assets/card_sustainable.png",
  card_exploitative: "assets/card_exploitative.png",
  player_basecard: "assets/player_basecard.png",
};

const HUD_HEIGHT = 250;
const BORDER_HEIGHT = 3;
const TOTAL_HUD = HUD_HEIGHT + BORDER_HEIGHT;

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
  private sustainableHolder!: Phaser.GameObjects.Image;
  private exploitativeHolder!: Phaser.GameObjects.Image;
  private username = "";
  private lobbyCode = "MAIN";
  private socket?: WebSocket;

  private sustainableCount = 0;
  private exploitativeCount = 0;
  private resizeHandler?: () => void;

  constructor() {
    super({ key: "BoardGameScene" });
  }

  preload() {
    this.load.image("board_bg", ASSETS.board_bg);
    this.load.image("card_sustainable", ASSETS.card_sustainable);
    this.load.image("card_exploitative", ASSETS.card_exploitative);
    this.load.image("player_basecard", ASSETS.player_basecard);
  }

  create() {
    const data = (this.scene.settings.data as BoardSceneData | undefined) ?? {};
    this.username = (data.username ?? "").trim();
    this.lobbyCode = (data.lobbyCode ?? "MAIN").trim() || "MAIN";

    document.body.style.overflowX = "hidden";
    document.body.style.overflowY = "auto";
    document.documentElement.style.overflowX = "hidden";
    document.documentElement.style.overflowY = "auto";

    this.players = this.username ? [{ name: this.username }] : [];

    this.layoutScene();
    this.createHUD();
    this.createStatusPanel();

    this.resizeHandler = () => this.layoutScene();
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

    void this.syncLobbyState();
    this.connectWebSocket();
  }

  private layoutScene() {
    const width = window.innerWidth;
    const bgTex = this.textures.get("board_bg").getSourceImage();
    const bgAspect = bgTex.height / bgTex.width;
    const bgDisplayH = width * bgAspect;
    const totalH = Math.max(TOTAL_HUD + bgDisplayH, window.innerHeight);

    this.scale.resize(width, totalH);
    this.game.canvas.style.width = `${width}px`;
    this.game.canvas.style.height = `${totalH}px`;

    const oldBg = this.children.list.find(
      (c) => c instanceof Phaser.GameObjects.Image && c.texture.key === "board_bg"
    );
    if (oldBg) oldBg.destroy();

    const bg = this.add.image(width / 2, TOTAL_HUD + bgDisplayH / 2, "board_bg");
    bg.setDisplaySize(width, bgDisplayH);
    bg.setDepth(0);

    const dimOverlay = this.add.rectangle(
      width / 2,
      TOTAL_HUD + bgDisplayH / 2,
      width,
      bgDisplayH,
      0x353b42,
      0.8
    );
    dimOverlay.setDepth(1);

    const oldHudBg = this.children.list.find(
      (c) => c instanceof Phaser.GameObjects.Rectangle && (c as { name?: string }).name === "hud_bg_fill"
    );
    if (oldHudBg) oldHudBg.destroy();

    const hudBgFill = this.add.rectangle(width / 2, TOTAL_HUD / 2, width, TOTAL_HUD, 0x0d1b2a, 1);
    (hudBgFill as { name?: string }).name = "hud_bg_fill";
    hudBgFill.setDepth(0);

    this.layoutCardHolders(width, bgDisplayH);
  }

  private layoutCardHolders(width: number, bgDisplayH: number) {
    if (this.sustainableHolder) this.sustainableHolder.destroy();
    if (this.exploitativeHolder) this.exploitativeHolder.destroy();

    const holderY = TOTAL_HUD + bgDisplayH * 0.25;
    const leftCenterX = width * 0.25;
    const rightCenterX = width * 0.75;
    const targetW = width * 0.38;

    this.sustainableHolder = this.add.image(leftCenterX, holderY, "card_sustainable");
    const susTexW = this.sustainableHolder.texture.getSourceImage().width;
    this.sustainableHolder.setScale(targetW / susTexW);
    this.sustainableHolder.setDepth(5);

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
      flexWrap: "wrap",
      padding: "12px",
    });

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

    parent.appendChild(hud);
    this.hudEl = hud;
  }

  private createStatusPanel() {
    const existing = document.getElementById("board-status");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;
    const status = document.createElement("div");
    status.id = "board-status";
    Object.assign(status.style, {
      position: "absolute",
      top: `${TOTAL_HUD + 12}px`,
      right: "12px",
      zIndex: "110",
      padding: "12px 16px",
      background: "rgba(13, 27, 42, 0.9)",
      color: "#f4efe7",
      border: "2px solid #d4a843",
      borderRadius: "12px",
      fontFamily: '"Jersey 20", sans-serif',
      fontSize: "24px",
      lineHeight: "1.2",
      minWidth: "220px",
      boxShadow: "0 8px 20px rgba(0,0,0,0.35)",
    });
    parent.appendChild(status);
    this.statusEl = status;
    this.setStatus("Connecting to backend...");
  }

  private setStatus(message: string) {
    if (!this.statusEl) return;
    this.statusEl.innerHTML = `Player: ${this.username || "Unknown"}<br/>Lobby: ${this.lobbyCode}<br/>${message}`;
  }

  private async syncLobbyState() {
    try {
      const data = await getLobbyPlayers();
      this.updatePlayers(data.players.map((name) => ({ name })));
      this.setStatus(`Lobby synced (${data.players.length} players)`);
    } catch (error) {
      this.setStatus(
        error instanceof Error ? `Lobby sync failed: ${error.message}` : "Lobby sync failed"
      );
    }
  }

  private connectWebSocket() {
    if (!this.username) {
      this.setStatus("Missing player name");
      return;
    }

    this.socket?.close();
    const socket = createGameSocket(this.username);
    this.socket = socket;

    socket.addEventListener("open", () => {
      this.setStatus("WebSocket connected");
    });

    socket.addEventListener("message", (event) => {
      try {
        const message = JSON.parse(event.data) as SocketMessage;

        if (message.type === "lobby_update") {
          const players = Array.isArray(message.data?.players)
            ? (message.data.players as string[])
            : [];
          this.updatePlayers(players.map((name) => ({ name })));
          this.setStatus(`Live lobby update (${players.length} players)`);
          return;
        }

        if (message.type === "player_disconnected") {
          const disconnectedUser = String(message.data?.username ?? "A player");
          this.setStatus(`${disconnectedUser} disconnected`);
          return;
        }

        if (message.type === "error") {
          const backendMessage = String(message.data?.message ?? "Unknown backend error");
          this.setStatus(`Backend error: ${backendMessage}`);
        }
      } catch {
        this.setStatus("Received invalid socket message");
      }
    });

    socket.addEventListener("close", () => {
      if (this.socket === socket) {
        this.setStatus("WebSocket disconnected");
      }
    });

    socket.addEventListener("error", () => {
      this.setStatus("WebSocket connection failed");
    });
  }

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

  private cleanup() {
    const username = this.username;

    if (this.socket) {
      this.socket.close();
      this.socket = undefined;
    }

    if (username) {
      void leaveLobby(username).catch(() => undefined);
    }

    if (this.hudEl) {
      this.hudEl.remove();
      this.hudEl = undefined;
    }

    if (this.statusEl) {
      this.statusEl.remove();
      this.statusEl = undefined;
    }

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
  }
}
