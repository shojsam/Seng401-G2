/**
 * game/GameState.ts — Shared types and mutable game state for BoardGameScene.
 */

export interface PlayerData {
  name: string;
  role?: string;
  isActive?: boolean;
  isEliminated?: boolean;
  characterId?: number; // 1-8, maps to assets/character{N}.png
}

export type BoardSceneData = {
  username?: string;
  lobbyCode?: string;
};

export type SocketMessage = {
  type?: string;
  data?: Record<string, unknown>;
};

export interface EnactedPolicy {
  title: string;
  description: string;
  policy_type: "sustainable" | "exploitative";
}

/**
 * Holds all mutable game state that the various subsystems read/write.
 * Owned by BoardGameScene and passed by reference to helpers.
 */
export class GameState {
  players: PlayerData[] = [];
  username = "";
  lobbyCode = "MAIN";

  sustainableCount = 0;
  exploitativeCount = 0;
  policyDrawCount = 20;

  myRole = "";
  currentLeader = "";
  currentVice = "";
  exploiterIds: string[] = [];
  gamePhase = "lobby";
  myCharacterId = 0;
  playerCharacters: Record<string, number> = {};

  // Enacted policies in order — used to fill policy holder slots
  enactedSustainable: EnactedPolicy[] = [];
  enactedExploitative: EnactedPolicy[] = [];

  // Character selection progress text
  characterProgress = "";

  // Voting results — stores each player's vote after election resolves
  // Key = player name, value = "approve" | "reject"
  playerVotes: Record<string, string> = {};
  lastElectionApproved: boolean | null = null;

  // Pending hand data — stored when leader_hand / vice_hand arrives
  // before the phase announcement finishes, so it can be re-shown after
  pendingLeaderHand: { title: string; description: string }[] | null = null;
  pendingViceHand: { title: string; description: string }[] | null = null;
}