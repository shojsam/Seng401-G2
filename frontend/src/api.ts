const DEFAULT_API_BASE = "https://seng401-g2-production.up.railway.app";

const trimTrailingSlash = (value: string) => value.replace(/\/+$/, "");

export const API_BASE = trimTrailingSlash(
  (import.meta.env.VITE_API_URL as string | undefined) || DEFAULT_API_BASE
);

export const WS_BASE = (() => {
  const configured = (import.meta.env.VITE_WS_URL as string | undefined)?.trim();
  if (configured) {
    return trimTrailingSlash(configured);
  }

  if (API_BASE.startsWith("https://")) {
    return `wss://${API_BASE.slice("https://".length)}`;
  }
  if (API_BASE.startsWith("http://")) {
    return `ws://${API_BASE.slice("http://".length)}`;
  }
  return API_BASE;
})();

type JoinLobbyResponse = {
  message: string;
  username: string;
};

type LobbyPlayersResponse = {
  players: string[];
};

async function parseError(response: Response) {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") {
      return body.detail;
    }
  } catch {
    // Ignore parse errors and fall back to status text.
  }

  return response.statusText || "Request failed";
}

export async function joinLobby(username: string) {
  const response = await fetch(`${API_BASE}/lobby/join`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as JoinLobbyResponse;
}

export async function leaveLobby(username: string) {
  const response = await fetch(`${API_BASE}/lobby/leave`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}

export async function getLobbyPlayers() {
  const response = await fetch(`${API_BASE}/lobby/players`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as LobbyPlayersResponse;
}

export function createGameSocket(username: string) {
  return new WebSocket(`${WS_BASE}/ws/${encodeURIComponent(username)}`);
}
