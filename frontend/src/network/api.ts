import { API_BASE } from "../config";

export async function register(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

export async function getLobbies() {
  const res = await fetch(`${API_BASE}/lobbies`);
  return res.json();
}

export async function createLobby() {
  const res = await fetch(`${API_BASE}/lobbies`, { method: "POST" });
  return res.json();
}

export async function joinLobby(lobbyId: string) {
  const res = await fetch(`${API_BASE}/lobbies/${lobbyId}/join`, {
    method: "POST",
  });
  return res.json();
}
