/**
 * game/GameSocketHandler.ts — WebSocket connection, message routing, and event handlers.
 */
import Phaser from "phaser";
import { createGameSocket, getLobbyPlayers } from "../src/api";
import type { GameState, SocketMessage } from "./GameState";
import { updatePhaseBar } from "./HUDBuilder";
import { hideAllOverlays } from "./OverlayManager";
import { announcePhase, dismissAnnouncer } from "./PhaseAnnouncer";

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

// ─── Message hold / deferral state ──────────────────────────────
// Messages can be held during:
//   1. Voting results display (5 seconds)
//   2. Phase announcement overlay (~3 seconds)
// Held messages are queued and replayed in order once the hold ends.
let holdActive = false;
let deferredMessages: {
  msg: SocketMessage;
  scene: Phaser.Scene;
  state: GameState;
  sendMessage: (type: string, data?: Record<string, unknown>) => void;
  ui: SocketUICallbacks;
}[] = [];

// Message types that should be deferred during any hold
const DEFERRED_TYPES = new Set([
  "phase_change",
  "leader_hand",
  "vice_hand",
  "nomination",
  "round_result",
]);

/**
 * Begin a hold period. Messages in DEFERRED_TYPES will be queued.
 * After `durationMs`, the hold ends and queued messages replay.
 * On replay, phase_change messages are processed first so their
 * announcements can re-defer leader_hand / vice_hand messages.
 */
function beginHold(durationMs: number) {
  holdActive = true;

  setTimeout(() => {
    holdActive = false;

    // Sort: phase_change first, then everything else in original order.
    // This ensures announcements fire before overlay-triggering messages,
    // so the new announcement's hold can re-queue them.
    const queued = [...deferredMessages];
    deferredMessages = [];

    const phaseChanges = queued.filter((e) => e.msg.type === "phase_change");
    const others = queued.filter((e) => e.msg.type !== "phase_change");

    for (const entry of phaseChanges) {
      handleSocketMessage(entry.msg, entry.scene, entry.state, entry.sendMessage, entry.ui);
    }
    for (const entry of others) {
      handleSocketMessage(entry.msg, entry.scene, entry.state, entry.sendMessage, entry.ui);
    }
  }, durationMs);
}

/** Cancel any active hold and discard queued messages. */
function cancelHold() {
  holdActive = false;
  deferredMessages = [];
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

  // If a hold is active, queue messages that would show overlays
  // or change the phase so they don't interrupt the current display
  if (holdActive && DEFERRED_TYPES.has(type)) {
    deferredMessages.push({ msg, scene, state, sendMessage, ui });
    return;
  }

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
      onElectionResult(data ?? {}, scene, state, ui);
      break;
    case "leader_hand":
      onLeaderHand(data ?? {}, scene, state);
      break;
    case "vice_hand":
      onViceHand(data ?? {}, scene, state);
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
    case "next_round_progress":
      onNextRoundProgress(data ?? {}, state, ui);
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

  // Reset next round state when moving to a new phase
  state.nextRoundReady = false;
  state.nextRoundProgress = "";

  updatePhaseBar(ui.getPhaseBarEl(), state);

  if (data.sustainable_count !== undefined) {
    state.sustainableCount = Number(data.sustainable_count);
  }
  if (data.exploiter_count !== undefined) {
    state.exploitativeCount = Number(data.exploiter_count);
  }

  ui.rebuildPolicyHolders();
  ui.rebuildHUD();

  // Show full-screen phase announcement and hold incoming messages
  // (like leader_hand, vice_hand) until it finishes
  const announceDuration = announcePhase(state.gamePhase, state);

  // Delay overlay triggers until after the announcement finishes.
  // If no announcement was shown (duration 0), fire immediately.
  const showOverlays = () => {
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

    // Re-show pending leader hand (Discard overlay) if it arrived early
    if (state.gamePhase === "leader_discard" && state.pendingLeaderHand) {
      const policies = state.pendingLeaderHand;
      state.pendingLeaderHand = null;
      const discardScene = scene.scene.get("DiscardPolicyScene") as
        { show: (d: { policies: typeof policies }) => void } | undefined;
      if (discardScene) discardScene.show({ policies });
    }

    // Re-show pending vice hand (Enact overlay) if it arrived early
    if (state.gamePhase === "vice_enact" && state.pendingViceHand) {
      const policies = state.pendingViceHand;
      state.pendingViceHand = null;
      const enactScene = scene.scene.get("PolicyEnactScene") as
        { show: (d: { policies: typeof policies }) => void } | undefined;
      if (enactScene) enactScene.show({ policies });
    }
  };

  if (announceDuration > 0) {
    // Hide any overlays that may have already been shown by
    // leader_hand / vice_hand arriving before this phase_change
    hideAllOverlays(scene);

    // Begin a hold so leader_hand / vice_hand arriving during the
    // announcement get queued and replayed after it finishes
    beginHold(announceDuration);
    setTimeout(showOverlays, announceDuration);
  } else {
    showOverlays();
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
  ui: SocketUICallbacks,
) {
  const approved = Boolean(data.approved);
  const votes = (data.votes ?? {}) as Record<string, string>;

  // Hide the voting overlay immediately
  const votingScene = scene.scene.get("VotingScene") as { hide: () => void } | undefined;
  if (votingScene) votingScene.hide();

  // Store votes and result in state for HUD display
  state.playerVotes = votes;
  state.lastElectionApproved = approved;

  // Enter the voting_results phase (client-side only)
  state.gamePhase = "voting_results";
  updatePhaseBar(ui.getPhaseBarEl(), state);
  ui.rebuildHUD();

  // Hold for 5 seconds — incoming phase_change / leader_hand
  // messages get queued and replayed after the hold ends.
  // Using a manual hold + setTimeout (real wall-clock time)
  // so the timer doesn't pause when the tab is inactive.
  holdActive = true;
  deferredMessages = [];

  setTimeout(() => {
    // Clear voting data
    state.playerVotes = {};
    state.lastElectionApproved = null;
    if (!approved) state.currentVice = "";

    holdActive = false;

    // Replay deferred messages — phase_change first so announcements
    // fire before overlay-triggering messages like leader_hand
    const queued = [...deferredMessages];
    deferredMessages = [];

    const phaseChanges = queued.filter((e) => e.msg.type === "phase_change");
    const others = queued.filter((e) => e.msg.type !== "phase_change");

    for (const entry of phaseChanges) {
      handleSocketMessage(entry.msg, entry.scene, entry.state, entry.sendMessage, entry.ui);
    }
    for (const entry of others) {
      handleSocketMessage(entry.msg, entry.scene, entry.state, entry.sendMessage, entry.ui);
    }

    // If no deferred messages updated things, rebuild to clear badges
    ui.rebuildHUD();
    updatePhaseBar(ui.getPhaseBarEl(), state);
  }, 5000);
}

function onLeaderHand(data: Record<string, unknown>, scene: Phaser.Scene, state: GameState) {
  const cards = Array.isArray(data.cards)
    ? (data.cards as { title?: string; description?: string; policy_type?: string }[])
    : [];
  const policies = cards.map((c) => ({
    title: String(c.title ?? c.policy_type ?? "Policy"),
    description: String(c.description ?? ""),
  }));

  // Store in state so it can be re-shown after announcement
  state.pendingLeaderHand = policies;

  const discardScene = scene.scene.get("DiscardPolicyScene") as
    { show: (d: { policies: typeof policies }) => void } | undefined;
  if (discardScene) discardScene.show({ policies });
}

function onViceHand(data: Record<string, unknown>, scene: Phaser.Scene, state: GameState) {
  const cards = Array.isArray(data.cards)
    ? (data.cards as { title?: string; description?: string; policy_type?: string }[])
    : [];
  const policies = cards.map((c) => ({
    title: String(c.title ?? c.policy_type ?? "Policy"),
    description: String(c.description ?? ""),
  }));

  // Store in state so it can be re-shown after announcement
  state.pendingViceHand = policies;

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

  let policyTitle = "Policy";
  if (enacted) {
    policyTitle = String(enacted.title ?? "Policy");
    const policy = {
      title: policyTitle,
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

  // Set phase to "resolution" so the Next Round button appears
  state.gamePhase = "resolution";
  updatePhaseBar(ui.getPhaseBarEl(), state);

  ui.rebuildPolicyHolders();
  ui.rebuildDrawPile();

  // Show "POLICY ENACTED" announcement and hold the next phase_change
  const policyType = enacted?.policy_type ?? "";
  const subtitle = policyType === "sustainable"
    ? `${policyTitle} — A sustainable policy was enacted.`
    : policyType === "exploitative"
      ? `${policyTitle} — An exploitative policy was enacted.`
      : `${policyTitle} has been enacted.`;

  const announceDuration = announcePhase("resolution", state, subtitle);
  if (announceDuration > 0) {
    beginHold(announceDuration);
  }
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
  dismissAnnouncer();
  announcePhase("game_over", state);
  ui.rebuildHUD();
}

function onGameReset(
  scene: Phaser.Scene,
  state: GameState,
  ui: SocketUICallbacks,
) {
  // Cancel any active hold
  cancelHold();

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
  state.playerVotes = {};
  state.lastElectionApproved = null;
  state.pendingLeaderHand = null;
  state.pendingViceHand = null;
  state.nextRoundProgress = "";
  state.nextRoundReady = false;

  hideAllOverlays(scene);
  dismissAnnouncer();
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

function onNextRoundProgress(
  data: Record<string, unknown>,
  state: GameState,
  ui: SocketUICallbacks,
) {
  const ready = Number(data.ready ?? 0);
  const total = Number(data.total ?? 0);
  state.nextRoundProgress = `${ready}/${total} PLAYERS READY`;
  updatePhaseBar(ui.getPhaseBarEl(), state);
}