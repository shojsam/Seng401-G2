const DEFAULT_API_BASE = "https://seng401-g2-production.up.railway.app";

const trimTrailingSlash = (value: string) => value.replace(/\/+$/, "");
const normalizeLobbyCode = (value: string) => value.trim().toUpperCase();

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

type LobbyResponse = {
  message: string;
  username: string;
  lobby_code: string;
};

type LobbyPlayersResponse = {
  lobby_code: string;
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

export async function createLobby(username: string) {
  const response = await fetch(`${API_BASE}/lobby/create`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as LobbyResponse;
}

export async function joinLobby(username: string, lobbyCode: string) {
  const response = await fetch(`${API_BASE}/lobby/join`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      lobby_code: normalizeLobbyCode(lobbyCode),
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }

  return (await response.json()) as LobbyResponse;
}

export async function leaveLobby(username: string, lobbyCode: string) {
  const response = await fetch(`${API_BASE}/lobby/leave`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      username,
      lobby_code: normalizeLobbyCode(lobbyCode),
    }),
  });

  if (!response.ok) {
    throw new Error(await parseError(response));
  }
}

export async function getLobbyPlayers(lobbyCode: string) {
  const response = await fetch(
    `${API_BASE}/lobby/${encodeURIComponent(normalizeLobbyCode(lobbyCode))}/players`
  );
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as LobbyPlayersResponse;
}

export function createGameSocket(lobbyCode: string, username: string) {
  return new WebSocket(
    `${WS_BASE}/ws/${encodeURIComponent(normalizeLobbyCode(lobbyCode))}/${encodeURIComponent(username)}`
  );
}
