import Phaser from "phaser";
import { MenuScene } from "./scenes/MenuScene";
import { BoardGameScene } from "./scenes/BoardGameScene";
import { RoleScene } from "./scenes/RoleScene";
import { VotingScene } from "./scenes/VotingScene";
import { NominationScene } from "./scenes/NominationScene";

const config: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: "game-container",
  width: 1280,
  height: 720,
  scale: {
    mode: Phaser.Scale.RESIZE,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    },
    input: {
        mouse: {
        preventDefaultWheel: false,
        },
    },
    backgroundColor: "#0d1b2a",
  scene: [MenuScene, BoardGameScene, RoleScene, VotingScene, NominationScene],
};

new Phaser.Game(config);