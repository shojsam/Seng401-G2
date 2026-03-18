import random
import string
from dataclasses import dataclass, field

from fastapi import WebSocket

from ..logic.game_engine import GameState
from ..logic.game_engine import Phase

LOBBY_CODE_LENGTH = 6
LOBBY_CODE_ALPHABET = string.ascii_uppercase + string.digits


@dataclass
class LobbyState:
    code: str
    players: set[str] = field(default_factory=set)
    active_connections: dict[str, WebSocket] = field(default_factory=dict)
    game_state: GameState | None = None


lobbies: dict[str, LobbyState] = {}


def normalize_lobby_code(lobby_code: str) -> str:
    return lobby_code.strip().upper()


def get_lobby(lobby_code: str) -> LobbyState | None:
    return lobbies.get(normalize_lobby_code(lobby_code))


def get_or_create_lobby(lobby_code: str) -> LobbyState:
    code = normalize_lobby_code(lobby_code)
    lobby = lobbies.get(code)
    if lobby is None:
        lobby = LobbyState(code=code)
        lobbies[code] = lobby
    return lobby


def create_lobby() -> LobbyState:
    while True:
        code = "".join(random.choices(LOBBY_CODE_ALPHABET, k=LOBBY_CODE_LENGTH))
        if code not in lobbies:
            lobby = LobbyState(code=code)
            lobbies[code] = lobby
            return lobby


def remove_player(lobby: LobbyState, username: str):
    lobby.players.discard(username)
    lobby.active_connections.pop(username, None)
    _delete_if_empty(lobby)


def reset_lobby(lobby: LobbyState):
    lobby.players.clear()
    lobby.game_state = None
    _delete_if_empty(lobby)


def _delete_if_empty(lobby: LobbyState):
    if lobby.players or lobby.active_connections:
        return
    if lobby.game_state is not None and lobby.game_state.phase != Phase.GAME_OVER:
        return
    lobbies.pop(lobby.code, None)
