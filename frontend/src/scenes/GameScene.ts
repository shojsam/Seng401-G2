import Phaser from "phaser";

export class GameScene extends Phaser.Scene {
  constructor() {
    super({ key: "GameScene" });
  }

  create() {
    const { width, height } = this.scale;

    this.add
      .text(width / 2, 40, "Game In Progress", {
        fontSize: "32px",
        color: "#4ecca3",
      })
      .setOrigin(0.5);

    // TODO: render game board, policy cards, voting UI, chat, turn indicator
  }
}
