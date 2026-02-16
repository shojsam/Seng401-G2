import Phaser from "phaser";
import { joinLobby } from "../network/api";

export class MenuScene extends Phaser.Scene {
  constructor() {
    super({ key: "MenuScene" });
  }

  create() {
    const { width, height } = this.scale;

    this.add
      .text(width / 2, height / 4, "GreenWatch", {
        fontSize: "48px",
        color: "#4ecca3",
      })
      .setOrigin(0.5);

    this.add
      .text(width / 2, height / 2 - 60, "Enter your username:", {
        fontSize: "22px",
        color: "#ffffff",
      })
      .setOrigin(0.5);

    // Create an HTML input element for username entry
    const input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Username";
    input.maxLength = 20;
    input.style.cssText =
      "position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); " +
      "font-size:20px; padding:10px 16px; width:240px; text-align:center; " +
      "border:2px solid #4ecca3; border-radius:8px; background:#1a1a2e; color:#fff; outline:none;";
    document.body.appendChild(input);
    input.focus();

    const joinBtn = this.add
      .text(width / 2, height / 2 + 40, "[ Join Game ]", {
        fontSize: "28px",
        color: "#ffffff",
      })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });

    const errorText = this.add
      .text(width / 2, height / 2 + 90, "", {
        fontSize: "18px",
        color: "#ff6b6b",
      })
      .setOrigin(0.5);

    const handleJoin = async () => {
      const username = input.value.trim();
      if (!username) {
        errorText.setText("Please enter a username");
        return;
      }
      try {
        const res = await joinLobby(username);
        if (res.username) {
          input.remove();
          this.scene.start("LobbyScene", { username });
        } else {
          errorText.setText(res.detail || "Could not join");
        }
      } catch {
        errorText.setText("Server not reachable");
      }
    };

    joinBtn.on("pointerdown", handleJoin);
    input.addEventListener("keydown", (e: KeyboardEvent) => {
      if (e.key === "Enter") handleJoin();
    });

    this.events.on("shutdown", () => input.remove());
  }
}
