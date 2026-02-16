import { API_BASE } from "../config";

export async function joinLobby(username: string) {
  const res = await fetch(`${API_BASE}/lobby/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  return res.json();
}

export async function leaveLobby(username: string) {
  const res = await fetch(`${API_BASE}/lobby/leave`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username }),
  });
  return res.json();
}

export async function getPlayers() {
  const res = await fetch(`${API_BASE}/lobby/players`);
  return res.json();
}
