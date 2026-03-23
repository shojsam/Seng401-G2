import random
import string
from dataclasses import dataclass, field

from fastapi import WebSocket
from mysql.connector import IntegrityError

from ..logic.game_engine import GameState
from ..logic.game_engine import Phase
from ..data.database import get_connection

LOBBY_CODE_LENGTH = 6
LOBBY_CODE_ALPHABET = string.ascii_uppercase + string.digits


@dataclass
class LobbyState:
    code: str
    players: set[str] = field(default_factory=set)
    active_connections: dict[str, WebSocket] = field(default_factory=dict)
    ready_players: set[str] = field(default_factory=set)
    game_state: GameState | None = None


lobbies: dict[str, LobbyState] = {}


class LobbyPlayerExistsError(ValueError):
    pass


def normalize_lobby_code(lobby_code: str) -> str:
    return lobby_code.strip().upper()


def get_lobby(lobby_code: str) -> LobbyState | None:
    code = normalize_lobby_code(lobby_code)
    if not code:
        return None

    players = _fetch_lobby_players(code)
    if players is None:
        lobbies.pop(code, None)
        return None

    lobby = lobbies.get(code)
    if lobby is None:
        lobby = LobbyState(code=code)
        lobbies[code] = lobby

    lobby.players = players
    return lobby


def get_or_create_lobby(lobby_code: str) -> LobbyState:
    code = normalize_lobby_code(lobby_code)
    lobby = get_lobby(code)
    if lobby is not None:
        return lobby

    _create_lobby_record(code)
    lobby = LobbyState(code=code)
    lobbies[code] = lobby
    return lobby


def create_lobby() -> LobbyState:
    while True:
        code = "".join(random.choices(LOBBY_CODE_ALPHABET, k=LOBBY_CODE_LENGTH))
        if _create_lobby_record(code):
            lobby = LobbyState(code=code)
            lobbies[code] = lobby
            return lobby


def add_player(lobby_code: str, username: str) -> LobbyState | None:
    code = normalize_lobby_code(lobby_code)
    if not code:
        return None

    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT lobby_id FROM lobbies WHERE lobby_code = %s", (code,))
        row = cursor.fetchone()
        if row is None:
            return None

        try:
            cursor.execute(
                "INSERT INTO lobby_players (lobby_id, username) VALUES (%s, %s)",
                (row[0], username),
            )
        except IntegrityError:
            connection.rollback()
            raise LobbyPlayerExistsError(username)

        connection.commit()
    finally:
        cursor.close()
        connection.close()

    lobby = get_lobby(code)
    if lobby is not None:
        lobby.ready_players.discard(username)
    return lobby


def get_lobby_players(lobby_code: str) -> list[str] | None:
    players = _fetch_lobby_players(lobby_code)
    if players is None:
        return None
    return sorted(players)


def remove_player(lobby: LobbyState, username: str):
    lobby.active_connections.pop(username, None)
    lobby.ready_players.discard(username)
    _remove_player_record(lobby.code, username)
    refreshed = get_lobby(lobby.code)
    if refreshed is None:
        lobby.players.clear()
        lobby.ready_players.clear()
        return
    lobby.players = refreshed.players
    lobby.ready_players.intersection_update(lobby.players)
    _delete_if_empty(lobby)


def reset_lobby(lobby: LobbyState):
    lobby.ready_players.clear()
    lobby.game_state = None


def _delete_if_empty(lobby: LobbyState):
    if lobby.players or lobby.active_connections:
        return
    if lobby.game_state is not None and lobby.game_state.phase != Phase.GAME_OVER:
        return
    _delete_lobby_record(lobby.code)
    lobbies.pop(lobby.code, None)


def _fetch_lobby_players(lobby_code: str) -> set[str] | None:
    code = normalize_lobby_code(lobby_code)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT lp.username
            FROM lobbies l
            LEFT JOIN lobby_players lp ON lp.lobby_id = l.lobby_id
            WHERE l.lobby_code = %s
            ORDER BY lp.joined_at ASC, lp.lobby_player_id ASC
            """,
            (code,),
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        return {row[0] for row in rows if row[0]}
    finally:
        cursor.close()
        connection.close()


def _create_lobby_record(code: str) -> bool:
    connection = get_connection()
    cursor = connection.cursor()
    try:
        try:
            cursor.execute("INSERT INTO lobbies (lobby_code) VALUES (%s)", (code,))
            connection.commit()
            return True
        except IntegrityError:
            connection.rollback()
            return False
    finally:
        cursor.close()
        connection.close()


def _remove_player_record(lobby_code: str, username: str):
    code = normalize_lobby_code(lobby_code)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            DELETE lp
            FROM lobby_players lp
            INNER JOIN lobbies l ON l.lobby_id = lp.lobby_id
            WHERE l.lobby_code = %s AND lp.username = %s
            """,
            (code, username),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def _delete_lobby_record(lobby_code: str):
    code = normalize_lobby_code(lobby_code)
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM lobbies WHERE lobby_code = %s", (code,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()
