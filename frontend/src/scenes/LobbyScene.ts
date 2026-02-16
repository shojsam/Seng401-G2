import Phaser from "phaser";

export class LobbyScene extends Phaser.Scene {
  constructor() {
    super({ key: "LobbyScene" });
  }

  create() {
    const { width, height } = this.scale;

    this.add
      .text(width / 2, 40, "Lobby", {
        fontSize: "32px",
        color: "#4ecca3",
      })
      .setOrigin(0.5);

    // TODO: show player list, ready button, start game button
    this.add
      .text(width / 2, height / 2, "Waiting for players...", {
        fontSize: "20px",
        color: "#cccccc",
      })
      .setOrigin(0.5);
  }
}
