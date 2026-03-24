/**
 * game/HudBuilder.ts — Builds the top HUD (player cards + phase bar).
 */
import type { GameState, PlayerData } from "./GameState";

const ASSETS = {
  player_basecard: "assets/player_basecard.png",
};

const HUD_HEIGHT = 250;
const PHASE_BAR_HEIGHT = 50;
const BORDER_HEIGHT = 5;
export const TOTAL_HUD = HUD_HEIGHT + PHASE_BAR_HEIGHT + BORDER_HEIGHT;

export function createHUD(
  state: GameState,
  baseWidth: number,
  createScaledWrapper: (id: string, zIndex: string) => { wrapper: HTMLDivElement; inner: HTMLDivElement },
): { hudWrapper: HTMLDivElement; phaseBarEl: HTMLDivElement } {
  const existing = document.getElementById("board-hud-wrapper");
  if (existing) existing.remove();

  const parent = document.getElementById("game-container") ?? document.body;
  const { wrapper, inner } = createScaledWrapper("board-hud-wrapper", "100");
  wrapper.style.pointerEvents = "auto";
  // Limit height so the HUD wrapper doesn't cover the board area below
  // Add extra for borders (content-box) and box-shadow
  const scale = parseFloat(inner.style.transform.match(/scale\(([^)]+)\)/)?.[1] ?? "1");
  const hudTotalPx = HUD_HEIGHT + BORDER_HEIGHT + PHASE_BAR_HEIGHT + BORDER_HEIGHT + 30;
  wrapper.style.height = `${hudTotalPx * scale}px`;

  const hud = document.createElement("div");
  hud.id = "board-hud";
  Object.assign(hud.style, {
    width: `${baseWidth}px`,
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
  state.players.forEach((player) => {
    const card = buildPlayerCard(player, state);
    hud.appendChild(card);
  });

  // ── Lobby code (top-left) ─────────────────────────────────────
  const lobbyCodeEl = document.createElement("div");
  lobbyCodeEl.id = "board-lobby-code";
  lobbyCodeEl.innerHTML =
    `<span style="color:#e8e4dc">Lobby Code:</span> ` +
    `<span style="color:#d4a843">${state.lobbyCode}</span>`;
  Object.assign(lobbyCodeEl.style, {
    position: "absolute",
    top: "10px",
    left: "14px",
    fontFamily: '"Jersey 20", sans-serif',
    fontSize: "32px",
    letterSpacing: "2px",
    lineHeight: "1.4",
    pointerEvents: "auto",
    cursor: "text",
    userSelect: "text",
    WebkitUserSelect: "text",
  });
  hud.appendChild(lobbyCodeEl);

  inner.appendChild(hud);

  // ── Phase bar ─────────────────────────────────────────────────
  const phaseBar = document.createElement("div");
  phaseBar.id = "board-phase-bar";
  Object.assign(phaseBar.style, {
    width: `${baseWidth}px`,
    height: `${PHASE_BAR_HEIGHT}px`,
    background: "#3a2518",
    borderBottom: `${BORDER_HEIGHT}px solid #d4a843`,
    boxSizing: "content-box",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontFamily: '"Jersey 20", sans-serif',
    position: "relative",
  });

  const phaseText = document.createElement("div");
  phaseText.id = "phase-text";
  Object.assign(phaseText.style, {
    fontSize: "28px",
    color: "#d4a843",
    letterSpacing: "2px",
    textTransform: "uppercase",
    textAlign: "center",
  });
  phaseText.textContent = getPhaseDisplayText(state);
  phaseBar.appendChild(phaseText);

  inner.appendChild(phaseBar);

  parent.appendChild(wrapper);

  return { hudWrapper: wrapper, phaseBarEl: phaseBar };
}

// ─── Player card builder ────────────────────────────────────────

function buildPlayerCard(player: PlayerData, state: GameState): HTMLDivElement {
  const isLeader =
    state.currentLeader &&
    player.name === state.currentLeader &&
    state.gamePhase !== "lobby";

  const card = document.createElement("div");
  Object.assign(card.style, {
    width: "150px",
    height: "225px",
    backgroundImage: `url("${ASSETS.player_basecard}")`,
    backgroundSize: "cover",
    backgroundPosition: "center",
    backgroundRepeat: "no-repeat",
    border: isLeader ? "4px solid #d4a843" : "none",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "flex-end",
    paddingBottom: isLeader ? "11px" : "15px",
    boxSizing: "border-box",
    overflow: "hidden",
    boxShadow: isLeader ? "0 0 12px rgba(212, 168, 67, 0.5)" : "none",
    position: "relative",
  });

  // ── Vote badge (top-right corner, shown during voting_results phase) ──
  if (state.gamePhase === "voting_results" && state.playerVotes) {
    const vote = state.playerVotes[player.name];
    if (vote) {
      const isAye = vote === "approve";
      const badge = document.createElement("div");
      badge.textContent = isAye ? "AYE" : "NAY";
      Object.assign(badge.style, {
        position: "absolute",
        top: "6px",
        right: "6px",
        background: isAye ? "#4a7c3f" : "#842929",
        color: "#e8e4dc",
        fontSize: "18px",
        fontFamily: '"Jersey 20", sans-serif',
        letterSpacing: "1px",
        padding: "2px 8px",
        boxShadow: "2px 2px 0 rgba(0,0,0,0.4)",
        zIndex: "10",
        lineHeight: "1.2",
      });
      card.appendChild(badge);
    }
  }

  // Character sprite
  const charId = player.characterId || state.playerCharacters[player.name] || 0;
  if (charId > 0) {
    const charImg = document.createElement("img");
    charImg.src = `assets/character${charId}.png`;
    charImg.alt = player.name;
    charImg.draggable = false;
    Object.assign(charImg.style, {
      width: "84px",
      height: "112px",
      objectFit: "contain",
      imageRendering: "pixelated",
      pointerEvents: "none",
      marginBottom: "4px",
    });
    card.appendChild(charImg);
  }

  // Name
  const name = document.createElement("div");
  name.textContent = player.name;
  Object.assign(name.style, {
    fontSize: "30px",
    color: player.isEliminated ? "#666666" : "#514b3f",
    textDecoration: player.isEliminated ? "line-through" : "none",
  });

  // Role visibility
  const role = document.createElement("div");
  let roleText = "";
  let roleColor = "#514b3f";

  const isGameOver = state.gamePhase === "game_over";
  const isMe = player.name === state.username;
  const iAmExploiter = state.myRole === "exploiter";
  const playerIsExploiter = state.exploiterIds.includes(player.name);

  if (isGameOver && player.role) {
    roleText = player.role.toUpperCase();
    roleColor = player.role === "exploiter" ? "#842929" : "#66785a";
  } else if (isMe && state.myRole) {
    roleText = state.myRole.toUpperCase();
    roleColor = state.myRole === "exploiter" ? "#842929" : "#66785a";
  } else if (iAmExploiter && playerIsExploiter) {
    roleText = "EXPLOITER";
    roleColor = "#842929";
  }

  role.textContent = roleText;
  Object.assign(role.style, {
    fontSize: "26px",
    color: roleColor,
    marginTop: "5px",
    letterSpacing: roleText ? "1px" : "0",
    minHeight: "25px",
  });

  card.appendChild(name);
  card.appendChild(role);

  return card;
}

// ─── Phase display text ─────────────────────────────────────────

export function getPhaseDisplayText(state: GameState): string {
  switch (state.gamePhase) {
    case "lobby":
      return state.characterProgress || "Waiting for players to connect...";
    case "role_reveal":
      return "Role Reveal — Review your role";
    case "nomination":
      return state.username === state.currentLeader
        ? "Your turn — Nominate a Vice"
        : `${state.currentLeader || "Leader"} is nominating a Vice...`;
    case "election":
      return "Election — Vote on the Leader/Vice pair";
    case "voting_results": {
      // Show tally: e.g. "The tally was 4-1. The vote was successful."
      const votes = state.playerVotes;
      let ayeCount = 0;
      let nayCount = 0;
      for (const v of Object.values(votes)) {
        if (v === "approve") ayeCount++;
        else nayCount++;
      }
      const passed = state.lastElectionApproved;
      const resultWord = passed ? "successful" : "unsuccessful";
      return `The tally was ${ayeCount}-${nayCount}. The vote was ${resultWord}.`;
    }
    case "leader_discard":
      return state.username === state.currentLeader
        ? "Your turn — Discard 1 policy card"
        : `${state.currentLeader || "Leader"} is reviewing policy cards...`;
    case "vice_enact":
      return state.username === state.currentVice
        ? "Your turn — Enact a policy"
        : `${state.currentVice || "Vice"} is choosing a policy to enact...`;
    case "resolution":
      return "Policy enacted!";
    case "game_over":
      return "Game Over";
    default:
      return "· · ·";
  }
}

export function updatePhaseBar(phaseBarEl: HTMLDivElement | undefined, state: GameState) {
  const textEl = phaseBarEl?.querySelector("#phase-text") as HTMLDivElement | null;
  if (textEl) {
    textEl.textContent = getPhaseDisplayText(state);
  }
}