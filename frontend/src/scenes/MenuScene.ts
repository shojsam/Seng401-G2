import Phaser from "phaser";

export class MenuScene extends Phaser.Scene {
  constructor() {
    super({ key: "MenuScene" });
  }

  create() {
    const { width, height } = this.scale;

    this.add
      .text(width / 2, height / 3, "GreenWatch", {
        fontSize: "48px",
        color: "#4ecca3",
      })
      .setOrigin(0.5);

    const playBtn = this.add
      .text(width / 2, height / 2, "[ Play ]", {
        fontSize: "28px",
        color: "#ffffff",
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });

    playBtn.on("pointerdown", () => {
      this.scene.start("LobbyScene");
    });
  }
}
