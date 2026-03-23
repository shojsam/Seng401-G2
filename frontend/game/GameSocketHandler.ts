/**
 * game/GameSocketHandler.ts — WebSocket connection, message routing, and event handlers.
 */
import Phaser from "phaser";
import { createGameSocket, getLobbyPlayers } from "../src/api";
import type { GameState, SocketMessage } from "./GameState";
import { updatePhaseBar } from "./HUDBuilder";
import { hideAllOverlays } from "./OverlayManager";

/**
 * Callbacks that the socket handler uses to trigger UI rebuilds.
 * These are provided by BoardGameScene so the handler doesn't
 * need a direct reference to the scene's private methods.
 */
export interface SocketUICallbacks {
  rebuildHUD: () => void;
  rebuildPolicyHolders: () => void;
  rebuildDrawPile: () => void;
  updatePlayers: (names: string[]) => void;
  getPhaseBarEl: () => HTMLDivElement | undefined;
}

export function connectWebSocket(
  scene: Phaser.Scene,
  state: GameState,
  sendMessage: (type: string, data?: Record<string, unknown>) => void,
  ui: SocketUICallbacks,
): WebSocket {
  const socket = createGameSocket(state.lobbyCode, state.username);

  socket.addEventListener("message", (event) => {
    try {
      const msg = JSON.parse(event.data) as SocketMessage;
      handleSocketMessage(msg, scene, state, sendMessage, ui);
    } catch {
      // bad message
    }
  });

  return socket;
}

export async function syncLobbyState(state: GameState, ui: SocketUICallbacks) {
  try {
    const data = await getLobbyPlayers(state.lobbyCode);
    ui.updatePlayers(data.players);
  } catch {
    // sync failed
  }
}

// ─── Message router ─────────────────────────────────────────────

function handleSocketMessage(
  msg: SocketMessage,
  scene: Phaser.Scene,
  state: GameState,
  sendMessage: (type: string, data?: Record<string, unknown>) => void,
  ui: SocketUICallbacks,
) {
  const { type, data } = msg;
  if (!type) return;

  switch (type) {
    case "lobby_update": {
      const players = Array.isArray(data?.players) ? (data.players as string[]) : [];
      ui.updatePlayers(players);
      break;
    }
    case "game_started":
      onGameStarted(data ?? {}, scene, state, ui);
      break;
    case "phase_change":
      onPhaseChange(data ?? {}, scene, state, ui);
      break;
    case "nomination":
      onNomination(data ?? {}, state);
      break;
    case "vote_acknowledged":
    case "vote_progress":
    case "role_ack_progress":
      break; // UI-only, handled by phase bar
    case "election_result":
      onElectionResult(data ?? {}, scene, state);
      break;
    case "leader_hand":
      onLeaderHand(data ?? {}, scene);
      break;
    case "vice_hand":
      onViceHand(data ?? {}, scene);
      break;
    case "round_result":
      onRoundResult(data ?? {}, scene, state, ui);
      break;
    case "game_over":
      onGameOver(data ?? {}, scene, state, ui);
      break;
    case "game_reset":
      onGameReset(scene, state, ui);
      break;
    case "character_update":
      onCharacterUpdate(data ?? {}, state, ui);
      break;
    case "character_progress":
      onCharacterProgress(data ?? {}, state, ui);
      break;
    case "player_disconnected":
    case "error":
      break;
    default:
      break;
  }
}

// ─── Individual handlers ────────────────────────────────────────

function onGameStarted(
  data: Record<string, unknown>,
  scene: Phaser.Scene,
  state: GameState,
  ui: SocketUICallbacks,
) {
  state.myRole = String(data.role ?? "");
  state.currentLeader = String(data.leader ?? "");
  state.exploiterIds = Array.isArray(data.exploiter_ids)
    ? (data.exploiter_ids as string[])
    : [];
  state.gamePhase = "role_reveal";
  updatePhaseBar(ui.getPhaseBarEl(), state);

  const players = Array.isArray(data.players) ? (data.players as string[]) : [];
  ui.updatePlayers(players);

  const roleScene = scene.scene.get("RoleScene") as
    { setRole: (r: string) => void; show: () => void } | undefined;
  if (roleScene) {
    roleScene.setRole(state.myRole as "reformer" | "exploiter");
    roleScene.show();
  }
}

function onPhaseChange(
  data: Record<string, unknown>,
  scene: Phaser.Scene,
  state: GameState,
  ui: SocketUICallbacks,
) {
  state.gamePhase = String(data.phase ?? "");
  if (data.leader) state.currentLeader = String(data.leader);
  if (data.nominated_vice) state.currentVice = String(data.nominated_vice);

  updatePhaseBar(ui.getPhaseBarEl(), state);

  if (data.sustainable_count !== undefined) {
    state.sustainableCount = Number(data.sustainable_count);
  }
  if (data.exploiter_count !== undefined) {
    state.exploitativeCount = Number(data.exploiter_count);
  }

  ui.rebuildPolicyHolders();
  ui.rebuildHUD();

  // Nomination: show overlay for leader
  if (state.gamePhase === "nomination" && state.username === state.currentLeader) {
    const iAmExploiter = state.myRole === "exploiter";
    const candidates = state.players
      .filter((p) => p.name !== state.username)
      .map((p) => {
        const charId = p.characterId || state.playerCharacters[p.name] || 0;
        const playerIsExploiter = state.exploiterIds.includes(p.name);
        let roleLabel = "";
        let roleColor = "";
        if (iAmExploiter && playerIsExploiter) {
          roleLabel = "EXPLOITER";
          roleColor = "#842929";
        }
        return { name: p.name, eligible: true, characterId: charId, roleLabel, roleColor };
      });

    const nominationScene = scene.scene.get("NominationScene") as
      { show: (d: { players: typeof candidates }) => void } | undefined;
    if (nominationScene) {
      nominationScene.show({ players: candidates });
    }
  }

  // Election: show voting overlay
  if (state.gamePhase === "election") {
    const nomineeCharId = state.playerCharacters[state.currentVice] || 0;
    const votingScene = scene.scene.get("VotingScene") as
      { show: (d: { nominatorName: string; nomineeName: string; nomineeCharacterId?: number }) => void } | undefined;
    if (votingScene) {
      votingScene.show({
        nominatorName: state.currentLeader,
        nomineeName: state.currentVice,
        nomineeCharacterId: nomineeCharId,
      });
    }
  }
}

function onNomination(data: Record<string, unknown>, state: GameState) {
  state.currentLeader = String(data.leader ?? "");
  state.currentVice = String(data.nominated_vice ?? "");
}

function onElectionResult(
  data: Record<string, unknown>,
  scene: Phaser.Scene,
  state: GameState,
) {
  const approved = Boolean(data.approved);
  const votingScene = scene.scene.get("VotingScene") as { hide: () => void } | undefined;
  if (votingScene) votingScene.hide();
  if (!approved) state.currentVice = "";
}

function onLeaderHand(data: Record<string, unknown>, scene: Phaser.Scene) {
  const cards = Array.isArray(data.cards)
    ? (data.cards as { title?: string; description?: string; policy_type?: string }[])
    : [];
  const policies = cards.map((c) => ({
    title: String(c.title ?? c.policy_type ?? "Policy"),
    description: String(c.description ?? ""),
  }));
  const discardScene = scene.scene.get("DiscardPolicyScene") as
    { show: (d: { policies: typeof policies }) => void } | undefined;
  if (discardScene) discardScene.show({ policies });
}

function onViceHand(data: Record<string, unknown>, scene: Phaser.Scene) {
  const cards = Array.isArray(data.cards)
    ? (data.cards as { title?: string; description?: string; policy_type?: string }[])
    : [];
  const policies = cards.map((c) => ({
    title: String(c.title ?? c.policy_type ?? "Policy"),
    description: String(c.description ?? ""),
  }));
  const enactScene = scene.scene.get("PolicyEnactScene") as
    { show: (d: { policies: typeof policies }) => void } | undefined;
  if (enactScene) enactScene.show({ policies });
}

function onRoundResult(
  data: Record<string, unknown>,
  scene: Phaser.Scene,
  state: GameState,
  ui: SocketUICallbacks,
) {
  state.sustainableCount = Number(data.sustainable_count ?? state.sustainableCount);
  state.exploitativeCount = Number(data.exploiter_count ?? state.exploitativeCount);
  state.policyDrawCount = Math.max(0, state.policyDrawCount - 3);

  // Store the enacted policy for display in the holder slots
  const enacted = data.enacted_policy as {
    title?: string;
    description?: string;
    policy_type?: string;
  } | undefined;

  if (enacted) {
    const policy = {
      title: String(enacted.title ?? "Policy"),
      description: String(enacted.description ?? ""),
      policy_type: enacted.policy_type as "sustainable" | "exploitative",
    };
    if (policy.policy_type === "sustainable") {
      state.enactedSustainable.push(policy);
    } else {
      state.enactedExploitative.push(policy);
    }
  }

  hideAllOverlays(scene);
  ui.rebuildPolicyHolders();
  ui.rebuildDrawPile();
}

function onGameOver(
  data: Record<string, unknown>,
  scene: Phaser.Scene,
  state: GameState,
  ui: SocketUICallbacks,
) {
  state.gamePhase = "game_over";
  updatePhaseBar(ui.getPhaseBarEl(), state);

  const summary = data.summary as { roles?: Record<string, string> } | undefined;
  if (summary?.roles) {
    state.players.forEach((p) => {
      p.role = summary.roles?.[p.name] ?? "?";
    });
  }

  hideAllOverlays(scene);
  ui.rebuildHUD();
}

function onGameReset(
  scene: Phaser.Scene,
  state: GameState,
  ui: SocketUICallbacks,
) {
  state.gamePhase = "lobby";
  updatePhaseBar(ui.getPhaseBarEl(), state);
  state.myRole = "";
  state.currentLeader = "";
  state.currentVice = "";
  state.exploiterIds = [];
  state.sustainableCount = 0;
  state.exploitativeCount = 0;
  state.policyDrawCount = 17;
  state.enactedSustainable = [];
  state.enactedExploitative = [];

  hideAllOverlays(scene);
  ui.rebuildHUD();
  ui.rebuildPolicyHolders();
  ui.rebuildDrawPile();
}

function onCharacterUpdate(
  data: Record<string, unknown>,
  state: GameState,
  ui: SocketUICallbacks,
) {
  const username = String(data.username ?? "");
  const characterId = Number(data.character_id ?? 0);
  if (username && characterId > 0) {
    state.playerCharacters[username] = characterId;
    const player = state.players.find((p) => p.name === username);
    if (player) player.characterId = characterId;
    ui.rebuildHUD();
  }
}

function onCharacterProgress(
  data: Record<string, unknown>,
  state: GameState,
  ui: SocketUICallbacks,
) {
  const selected = Number(data.selected ?? 0);
  const total = Number(data.total ?? 0);
  state.characterProgress = `${selected}/${total} players ready`;
  updatePhaseBar(ui.getPhaseBarEl(), state);
}