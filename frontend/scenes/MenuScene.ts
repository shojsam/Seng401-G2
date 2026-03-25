import Phaser from "phaser";
import { createLobby, joinLobby } from "../src/api";

/**
 * Asset paths — adjust these to match your project's asset directory.
 * You need to place the two images in your public/assets folder:
 *   - menu_bg.png        (the pixel-art landscape)
 *   - menu_logo.png      (the GREENWASHED banner + emblem with transparent bg)
 */
const ASSET_BG = "assets/menu_bg.png";
const ASSET_LOGO = "assets/menu_logo.png";

export class MenuScene extends Phaser.Scene {
  private containerEl?: HTMLDivElement;
  private injectedStyleEl?: HTMLStyleElement;

  constructor() {
    super({ key: "MenuScene" });
  }

  create() {
    this.cameras.main.setBackgroundColor("#1a2e1a");

    if (this.game.canvas) {
      this.game.canvas.style.display = "none";
    }

    this.createMenuHTML();

    this.events.on("shutdown", this.cleanup, this);
    this.events.on("destroy", this.cleanup, this);
  }

  private createMenuHTML() {
    const existing = document.getElementById("menu-scene-ui");
    if (existing) existing.remove();

    const parent = document.getElementById("game-container") ?? document.body;

    // ── Root container ──────────────────────────────────────────────
    const container = document.createElement("div");
    container.id = "menu-scene-ui";
    Object.assign(container.style, {
      position: "relative",
      width: "100%",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "flex-start",
      overflow: "hidden",
      fontFamily: `"Jersey 20", sans-serif`,
      color: "#f4efe7",
      boxSizing: "border-box",
      imageRendering: "pixelated",
    });

    // ── Background image (full-bleed) ───────────────────────────────
    const bg = document.createElement("div");
    Object.assign(bg.style, {
      position: "absolute",
      inset: "0",
      backgroundImage: `url("${ASSET_BG}")`,
      backgroundSize: "cover",
      backgroundPosition: "center",
      backgroundRepeat: "no-repeat",
      imageRendering: "pixelated",
      zIndex: "0",
    });
    container.appendChild(bg);

    // Slight dark overlay so panels pop against the background
    const overlay = document.createElement("div");
    Object.assign(overlay.style, {
      position: "absolute",
      inset: "0",
      background:
        "linear-gradient(to bottom, rgba(0,0,0,0.10) 0%, rgba(0,0,0,0.45) 100%)",
      zIndex: "1",
    });
    container.appendChild(overlay);

    // ── Content wrapper (above bg) ──────────────────────────────────
    const wrapper = document.createElement("div");
    Object.assign(wrapper.style, {
      position: "relative",
      zIndex: "2",
      width: "100%",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      paddingBottom: "40px",
    });

    // ── Logo / Banner ───────────────────────────────────────────────
    const logoWrap = document.createElement("div");
    Object.assign(logoWrap.style, {
      width: "100%",
      display: "flex",
      justifyContent: "center",
      marginTop: "20px",
      marginBottom: "10px",
    });

    const logo = document.createElement("img");
    logo.src = ASSET_LOGO;
    logo.alt = "GREENWASHED";
    Object.assign(logo.style, {
      maxWidth: "900px",
      width: "60%",
      height: "auto",
      objectFit: "contain",
      imageRendering: "pixelated",
      filter: "drop-shadow(0 4px 0 rgba(0,0,0,0.6))",
    });
    logoWrap.appendChild(logo);
    wrapper.appendChild(logoWrap);

    // ── Panels grid ─────────────────────────────────────────────────
    const grid = document.createElement("div");
    grid.classList.add("menu-grid");
    Object.assign(grid.style, {
      width: "100%",
      maxWidth: "1100px",
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: "28px",
      padding: "10px 28px 0",
      boxSizing: "border-box",
    });

    // ── JOIN SESSION panel ──────────────────────────────────────────
    const joinPanel = this.buildPanel("Join Session", "#2b9d65", "#2b9d65");

    joinPanel.appendChild(
      this.buildDescription(
        "Enter an existing lobby code and your player name to join the match."
      )
    );

    const lobbyLabel = this.buildLabel("Lobby Code");
    const lobbyInput = this.buildInput("Enter code", 8);
    const joinNameLabel = this.buildLabel("Player Name");
    const joinNameInput = this.buildInput("Enter your name", 12);
    const joinButton = this.buildButton(
      "Join Session",
      "#37935a",
      "#1a4a2a",
      "#e0b66a"
    );
    const joinMessage = this.buildMessage();

    joinButton.onclick = async () => {
      const lobby = lobbyInput.value.trim();
      const username = joinNameInput.value.trim();

      if (!lobby || !username) {
        joinMessage.style.color = "#ffd3c8";
        joinMessage.textContent = "Enter both a lobby code and player name.";
        return;
      }

      joinButton.disabled = true;
      joinMessage.style.color = "#ccf0c8";
      joinMessage.textContent = `Joining ${lobby} as ${username}...`;

      try {
        const result = await joinLobby(username, lobby);
        this.cleanup();
        this.scene.start("BoardGameScene", {
          username: result.username,
          lobbyCode: result.lobby_code,
        });
      } catch (error) {
        joinMessage.style.color = "#ffd3c8";
        joinMessage.textContent =
          error instanceof Error ? error.message : "Failed to join the lobby.";
      } finally {
        joinButton.disabled = false;
      }
    };

    const enterJoin = (e: KeyboardEvent) => {
      if (e.key === "Enter") joinButton.click();
    };

    lobbyInput.addEventListener("keydown", enterJoin);
    joinNameInput.addEventListener("keydown", enterJoin);

    joinPanel.append(
      lobbyLabel,
      lobbyInput,
      joinNameLabel,
      joinNameInput,
      joinButton,
      joinMessage
    );

    // ── CREATE SESSION panel ────────────────────────────────────────
    const createPanel = this.buildPanel("Create Session", "#2b9d65", "#2b9d65");

    createPanel.appendChild(
      this.buildDescription(
        "Start a new lobby and invite others to debate sustainability versus exploitation."
      )
    );

    const createNameLabel = this.buildLabel("Player Name");
    const createNameInput = this.buildInput("Enter your name", 12);
    const createButton = this.buildButton(
      "Create Session",
      "#37935a",
      "#1a4a2a",
      "#e0b66a"
    );
    const createMessage = this.buildMessage();

    createButton.onclick = async () => {
      const username = createNameInput.value.trim();

      if (!username) {
        createMessage.style.color = "#ffd3c8";
        createMessage.textContent = "Enter your player name first.";
        return;
      }

      createButton.disabled = true;
      createMessage.style.color = "#cfe2ff";
      createMessage.textContent = `Creating a new session for ${username}...`;

      try {
        const result = await createLobby(username);
        this.cleanup();
        this.scene.start("BoardGameScene", {
          username: result.username,
          lobbyCode: result.lobby_code,
        });
      } catch (error) {
        createMessage.style.color = "#ffd3c8";
        createMessage.textContent =
          error instanceof Error ? error.message : "Failed to create the lobby.";
      } finally {
        createButton.disabled = false;
      }
    };

    createNameInput.addEventListener("keydown", (e: KeyboardEvent) => {
      if (e.key === "Enter") createButton.click();
    });

    createPanel.append(createNameLabel, createNameInput, createButton, createMessage);

    grid.appendChild(joinPanel);
    grid.appendChild(createPanel);
    wrapper.appendChild(grid);

    // ── Footer tagline ──────────────────────────────────────────────
    const footer = document.createElement("div");
    footer.textContent = "A hidden-role sustainability strategy game.";
    Object.assign(footer.style, {
      marginTop: "24px",
      fontSize: "26px",
      color: "#d9c98d",
      fontFamily: `"Jersey 20", sans-serif`,
      fontWeight: "400",
      textAlign: "center",
      letterSpacing: "1px",
    });
    wrapper.appendChild(footer);

    container.appendChild(wrapper);
    parent.appendChild(container);
    this.containerEl = container;

    // ── Inject responsive breakpoint ────────────────────────────────
    const style = document.createElement("style");
    style.textContent = `
      #menu-scene-ui * {
        image-rendering: pixelated;
        image-rendering: -moz-crisp-edges;
        image-rendering: crisp-edges;
      }

      @media (max-width: 820px) {
        #menu-scene-ui .menu-grid {
          grid-template-columns: 1fr !important;
        }
      }

      #menu-scene-ui input::placeholder {
        color: #7b7b7b;
        opacity: 1;
        font-family: "Jersey 20", sans-serif;
        letter-spacing: 0.5px;
      }

      #menu-scene-ui button:hover {
        filter: brightness(1.12);
      }
    `;
    document.head.appendChild(style);
    this.injectedStyleEl = style;
  }

  // ── Helper builders ───────────────────────────────────────────────

  private buildPanel(title: string, borderColor: string, lineColor: string): HTMLDivElement {
    const panel = document.createElement("div");
    Object.assign(panel.style, {
      background: "rgba(42, 46, 51, 0.92)",
      border: `4px solid ${borderColor}`,
      padding: "26px 26px 28px",
      boxSizing: "border-box",
      boxShadow: "6px 6px 0 rgba(0,0,0,0.5)",
      imageRendering: "pixelated",
    });

    const heading = document.createElement("div");
    heading.textContent = title;
    Object.assign(heading.style, {
      fontSize: "48px",
      fontWeight: "400",
      textTransform: "uppercase",
      color: "#e8e4dc",
      marginBottom: "14px",
      letterSpacing: "1px",
      fontFamily: `"Jersey 20", sans-serif`,
    });

    const divider = document.createElement("div");
    Object.assign(divider.style, {
      width: "100%",
      height: "4px",
      background: lineColor,
      marginBottom: "16px",
    });

    panel.appendChild(heading);
    panel.appendChild(divider);
    return panel;
  }

  private buildDescription(text: string): HTMLDivElement {
    const desc = document.createElement("div");
    desc.textContent = text;
    Object.assign(desc.style, {
      fontFamily: `"Jersey 20", sans-serif`,
      fontSize: "24px",
      fontWeight: "400",
      lineHeight: "1.3",
      letterSpacing: "0.5px",
      color: "#9e9a92",
      marginBottom: "22px",
    });
    return desc;
  }

  private buildLabel(text: string): HTMLDivElement {
    const label = document.createElement("div");
    label.textContent = text;
    Object.assign(label.style, {
      fontSize: "30px",
      fontWeight: "400",
      color: "#e8e4dc",
      marginBottom: "6px",
      fontFamily: `"Jersey 20", sans-serif`,
      letterSpacing: "0.5px",
    });
    return label;
  }

  private buildInput(placeholder: string, maxLength: number): HTMLInputElement {
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = placeholder;
    input.maxLength = maxLength;

    Object.assign(input.style, {
      width: "100%",
      height: "62px",
      border: "3px solid #6b6355",
      background: "#e8e5df",
      color: "#232323",
      fontSize: "28px",
      fontWeight: "400",
      padding: "0 16px",
      boxSizing: "border-box",
      outline: "none",
      marginBottom: "18px",
      fontFamily: `"Jersey 20", sans-serif`,
      letterSpacing: "0.5px",
      boxShadow: "4px 4px 0 rgba(0,0,0,0.3)",
      imageRendering: "pixelated",
    });

    input.addEventListener("focus", () => {
      input.style.border = "3px solid #e0b66a";
      input.style.boxShadow = "4px 4px 0 rgba(0,0,0,0.3)";
    });

    input.addEventListener("blur", () => {
      input.style.border = "3px solid #6b6355";
      input.style.boxShadow = "4px 4px 0 rgba(0,0,0,0.3)";
    });

    return input;
  }

  private buildButton(
    text: string,
    bg: string,
    shadow: string,
    borderColor: string
  ): HTMLButtonElement {
    const btn = document.createElement("button");
    btn.textContent = text;

    Object.assign(btn.style, {
      width: "100%",
      height: "74px",
      border: `4px solid ${borderColor}`,
      background: bg,
      color: "#f0ebe3",
      fontSize: "34px",
      fontWeight: "400",
      textTransform: "uppercase",
      letterSpacing: "1px",
      cursor: "pointer",
      boxShadow: `4px 4px 0 ${shadow}`,
      fontFamily: `"Jersey 20", sans-serif`,
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

  private buildMessage(): HTMLDivElement {
    const msg = document.createElement("div");
    Object.assign(msg.style, {
      marginTop: "12px",
      minHeight: "22px",
      fontSize: "22px",
      fontWeight: "400",
      fontFamily: `"Jersey 20", sans-serif`,
      color: "#9e9a92",
      letterSpacing: "0.5px",
    });
    return msg;
  }

  // ── Cleanup ───────────────────────────────────────────────────────

  private cleanup() {
    if (this.containerEl) {
      this.containerEl.remove();
      this.containerEl = undefined;
    }

    if (this.injectedStyleEl) {
      this.injectedStyleEl.remove();
      this.injectedStyleEl = undefined;
    }

    if (this.game.canvas) {
      this.game.canvas.style.display = "block";
    }
  }
}