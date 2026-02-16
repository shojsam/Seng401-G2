import { WS_BASE } from "../config";

export class GameSocket {
  private socket: WebSocket | null = null;
  private handlers: Map<string, (data: any) => void> = new Map();

  connect(username: string) {
    this.socket = new WebSocket(`${WS_BASE}/ws/${username}`);

    this.socket.onopen = () => {
      console.log("WebSocket connected");
    };

    this.socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      const handler = this.handlers.get(message.type);
      if (handler) {
        handler(message.data);
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket disconnected");
    };
  }

  on(type: string, handler: (data: any) => void) {
    this.handlers.set(type, handler);
  }

  send(type: string, data: any = {}) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type, data }));
    }
  }

  disconnect() {
    this.socket?.close();
  }
}
