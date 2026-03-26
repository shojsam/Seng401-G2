/**
 * game/OverlayManager.ts — Wires overlay scene events to WebSocket messages.
 */
import Phaser from "phaser";
import type { GameState } from "./GameState";

export function setupOverlayListeners(
  scene: Phaser.Scene,
  state: GameState,
  sendMessage: (type: string, data?: Record<string, unknown>) => void,
) {
  // RoleScene → role acknowledged
  const roleScene = scene.scene.get("RoleScene");
  if (roleScene) {
    roleScene.events.on("role-acknowledged", () => {
      sendMessage("role_acknowledged");
    });
  }

  // CharacterSelectionScene → character selected
  const charScene = scene.scene.get("CharacterSelectionScene");
  if (charScene) {
    charScene.events.on("character-selected", (characterNumber: number, _username: string) => {
      state.myCharacterId = characterNumber;
      state.playerCharacters[state.username] = characterNumber;
      const me = state.players.find((p) => p.name === state.username);
      if (me) me.characterId = characterNumber;
      sendMessage("character_selected", { character_id: characterNumber });
    });
  }

  // NominationScene → nomination confirmed
  const nominationScene = scene.scene.get("NominationScene");
  if (nominationScene) {
    nominationScene.events.on("nomination-confirmed", (selectedName: string) => {
      sendMessage("nominate_vice", { vice_id: selectedName });
    });
  }

  // VotingScene → vote confirmed
  const votingScene = scene.scene.get("VotingScene");
  if (votingScene) {
    votingScene.events.on("vote-confirmed", (vote: string) => {
      const voteValue = vote === "aye" ? "approve" : "reject";
      sendMessage("cast_vote", { vote: voteValue });
    });
  }

  // DiscardPolicyScene → policy discarded
  const discardScene = scene.scene.get("DiscardPolicyScene");
  if (discardScene) {
    discardScene.events.on("policy-discarded", (_policy: unknown, index: number) => {
      sendMessage("leader_discard", { discard_index: index });
      const ds = scene.scene.get("DiscardPolicyScene") as { hide?: () => void } | undefined;
      if (ds?.hide) ds.hide();
    });
  }

  // PolicyEnactScene → policy enacted
  const enactScene = scene.scene.get("PolicyEnactScene");
  if (enactScene) {
    enactScene.events.on("policy-enacted", (_policy: unknown, index: number) => {
      sendMessage("vice_enact", { enact_index: index });
      const es = scene.scene.get("PolicyEnactScene") as { hide?: () => void } | undefined;
      if (es?.hide) es.hide();
    });
  }
}

export function hideAllOverlays(scene: Phaser.Scene) {
  const scenes = ["VotingScene", "NominationScene", "DiscardPolicyScene", "PolicyEnactScene"];
  for (const sceneName of scenes) {
    const s = scene.scene.get(sceneName) as { hide?: () => void } | undefined;
    if (s?.hide) s.hide();
  }
}