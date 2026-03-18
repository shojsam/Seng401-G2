import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..data.models import save_game_result
from ..logic.game_engine import GameState, Phase
from ..logic.voting import Vote
from ..state.lobbies import LobbyState, get_lobby, normalize_lobby_code, remove_player, reset_lobby

router = APIRouter()
logger = logging.getLogger(__name__)

DISCUSSION_SECONDS = 90


async def broadcast(lobby: LobbyState, message: dict):
    disconnected: list[str] = []
    for username, ws in lobby.active_connections.items():
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(username)

    for username in disconnected:
        remove_player(lobby, username)


async def send_to_player(lobby: LobbyState, username: str, message: dict):
    ws = lobby.active_connections.get(username)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            remove_player(lobby, username)


async def broadcast_lobby_state(lobby: LobbyState):
    players = list(lobby.players)
    await broadcast(
        lobby,
        {
            "type": "lobby_update",
            "data": {
                "lobby_code": lobby.code,
                "players": players,
                "count": len(players),
                "can_start": len(players) >= 5,
            },
        },
    )


def save_game_outcome(winner: str):
    try:
        save_game_result(winner)
    except Exception:
        logger.exception("Failed to save game outcome")


async def handle_start_game(lobby: LobbyState, username: str):
    game_state = lobby.game_state

    if game_state is not None and game_state.phase != Phase.GAME_OVER:
        await send_to_player(
            lobby,
            username,
            {"type": "error", "data": {"message": "A game is already in progress"}},
        )
        return

    if len(lobby.players) < 5:
        await send_to_player(
            lobby,
            username,
            {"type": "error", "data": {"message": "Need at least 5 players to start"}},
        )
        return

    lobby.game_state = GameState(list(lobby.players))
    game_state = lobby.game_state
    start_info = game_state.start_game()

    for pid in game_state.player_ids:
        role = start_info["roles"][pid]
        hand = game_state.get_hand(pid)

        private_msg: dict = {
            "type": "game_started",
            "data": {
                "lobby_code": lobby.code,
                "role": role,
                "hand": hand,
                "players": game_state.player_ids,
            },
        }

        if role == "exploiter":
            private_msg["data"]["exploiter_ids"] = start_info["exploiter_ids"]

        await send_to_player(lobby, pid, private_msg)

    await broadcast(
        lobby,
        {
            "type": "phase_change",
            "data": {
                "lobby_code": lobby.code,
                "phase": Phase.ROLE_REVEAL.value,
                "current_player": game_state.current_player,
                "turn_index": game_state.turn_index,
            },
        },
    )

    await asyncio.sleep(5)
    if lobby.game_state and lobby.game_state.phase == Phase.ROLE_REVEAL:
        lobby.game_state.phase = Phase.PROPOSAL
        await broadcast(
            lobby,
            {
                "type": "phase_change",
                "data": {
                    "lobby_code": lobby.code,
                    "phase": Phase.PROPOSAL.value,
                    "current_player": lobby.game_state.current_player,
                    "turn_index": lobby.game_state.turn_index,
                    "message": f"It is {lobby.game_state.current_player}'s turn to propose a policy.",
                },
            },
        )


async def handle_propose_policy(lobby: LobbyState, username: str, data: dict):
    game_state = lobby.game_state

    if game_state is None:
        await send_to_player(lobby, username, {"type": "error", "data": {"message": "No game in progress"}})
        return

    if game_state.phase != Phase.PROPOSAL:
        await send_to_player(lobby, username, {"type": "error", "data": {"message": "Not in proposal phase"}})
        return

    if username != game_state.current_player:
        await send_to_player(lobby, username, {"type": "error", "data": {"message": "It is not your turn to propose"}})
        return

    card_index = data.get("card_index", -1)
    try:
        policy = game_state.propose_policy(username, card_index)
    except ValueError as exc:
        await send_to_player(lobby, username, {"type": "error", "data": {"message": str(exc)}})
        return

    await broadcast(
        lobby,
        {
            "type": "policy_proposed",
            "data": {
                "lobby_code": lobby.code,
                "proposed_by": username,
                "policy": {
                    "name": policy.name,
                    "description": policy.description,
                },
            },
        },
    )

    game_state.begin_discussion()
    await broadcast(
        lobby,
        {
            "type": "phase_change",
            "data": {
                "lobby_code": lobby.code,
                "phase": Phase.DISCUSSION.value,
                "message": f"{username} proposed: {policy.name}. Discuss! ({DISCUSSION_SECONDS}s)",
                "timer_seconds": DISCUSSION_SECONDS,
            },
        },
    )

    asyncio.create_task(_discussion_timer(lobby.code))


async def _discussion_timer(lobby_code: str):
    await asyncio.sleep(DISCUSSION_SECONDS)
    lobby = get_lobby(lobby_code)
    if lobby and lobby.game_state and lobby.game_state.phase == Phase.DISCUSSION:
        await handle_begin_voting(lobby)


async def handle_begin_voting(lobby: LobbyState):
    if lobby.game_state is None:
        return

    lobby.game_state.begin_voting()
    await broadcast(
        lobby,
        {
            "type": "phase_change",
            "data": {
                "lobby_code": lobby.code,
                "phase": Phase.VOTING.value,
                "message": "Voting is now open. Approve or reject the proposed policy.",
            },
        },
    )


async def handle_cast_vote(lobby: LobbyState, username: str, data: dict):
    game_state = lobby.game_state

    if game_state is None:
        await send_to_player(lobby, username, {"type": "error", "data": {"message": "No game in progress"}})
        return

    if game_state.phase != Phase.VOTING:
        await send_to_player(lobby, username, {"type": "error", "data": {"message": "Not in voting phase"}})
        return

    if username in game_state.votes:
        await send_to_player(lobby, username, {"type": "error", "data": {"message": "You have already voted this round"}})
        return

    vote_value = str(data.get("vote", "")).lower()
    if vote_value not in ("approve", "reject"):
        await send_to_player(lobby, username, {"type": "error", "data": {"message": "Vote must be 'approve' or 'reject'"}})
        return

    vote = Vote.APPROVE if vote_value == "approve" else Vote.REJECT
    all_in = game_state.cast_vote(username, vote)

    await send_to_player(lobby, username, {"type": "vote_acknowledged", "data": {"vote": vote_value}})
    await broadcast(
        lobby,
        {
            "type": "vote_progress",
            "data": {
                "lobby_code": lobby.code,
                "votes_cast": len(game_state.votes),
                "votes_needed": len(game_state.player_ids),
            },
        },
    )

    if all_in:
        await _resolve_round(lobby)


async def _resolve_round(lobby: LobbyState):
    game_state = lobby.game_state
    if game_state is None:
        return

    result = game_state.resolve_round()
    approved = result["approved"]

    await broadcast(
        lobby,
        {
            "type": "round_result",
            "data": {
                "lobby_code": lobby.code,
                "approved": approved,
                "status": "accepted" if approved else "rejected",
                "votes": result["votes"],
                "policy": result["policy"],
                "enacted_sustainable": game_state.enacted_sustainable,
                "enacted_exploiter": game_state.enacted_exploiter,
                "message": (
                    f"Policy ACCEPTED! ({result['policy']['name']})"
                    if approved
                    else f"Policy REJECTED. ({result['policy']['name']})"
                ),
            },
        },
    )

    if result.get("winner"):
        winner = result["winner"]
        save_game_outcome(winner)
        await broadcast(
            lobby,
            {
                "type": "game_over",
                "data": {
                    "lobby_code": lobby.code,
                    "winner": winner,
                    "summary": game_state.get_summary(),
                    "message": (
                        "Reformers win! Sustainable policies prevailed."
                        if winner == "reformers"
                        else "Exploiters win! Exploitative policies dominated."
                    ),
                },
            },
        )
        return

    await asyncio.sleep(5)
    if lobby.game_state and lobby.game_state.phase != Phase.GAME_OVER:
        current = lobby.game_state.current_player
        hand = lobby.game_state.get_hand(current)

        if not hand:
            await broadcast(
                lobby,
                {
                    "type": "game_over",
                    "data": {
                        "lobby_code": lobby.code,
                        "winner": "draw",
                        "summary": lobby.game_state.get_summary(),
                        "message": "All policy cards have been played. Game ends in a draw.",
                    },
                },
            )
            save_game_outcome("draw")
            return

        lobby.game_state.phase = Phase.PROPOSAL
        await broadcast(
            lobby,
            {
                "type": "phase_change",
                "data": {
                    "lobby_code": lobby.code,
                    "phase": Phase.PROPOSAL.value,
                    "current_player": lobby.game_state.current_player,
                    "turn_index": lobby.game_state.turn_index,
                    "message": f"It is {lobby.game_state.current_player}'s turn to propose a policy.",
                },
            },
        )
        await send_to_player(lobby, current, {"type": "hand_update", "data": {"hand": hand}})


async def handle_skip_discussion(lobby: LobbyState, _username: str):
    if lobby.game_state and lobby.game_state.phase == Phase.DISCUSSION:
        await handle_begin_voting(lobby)


async def handle_reset_game(lobby: LobbyState, _username: str):
    reset_lobby(lobby)
    await broadcast(lobby, {"type": "game_reset", "data": {"lobby_code": lobby.code, "message": "Game has been reset. Return to lobby."}})


@router.websocket("/ws/{lobby_code}/{username}")
async def game_ws(websocket: WebSocket, lobby_code: str, username: str):
    username = username.strip()
    lobby = get_lobby(lobby_code)

    if lobby is None or not username:
        await websocket.close(code=1008)
        return

    if username not in lobby.players:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    lobby.active_connections[username] = websocket
    await broadcast_lobby_state(lobby)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            msg_data = data.get("data", {})

            if msg_type == "start_game":
                await handle_start_game(lobby, username)
            elif msg_type == "propose_policy":
                await handle_propose_policy(lobby, username, msg_data)
            elif msg_type == "cast_vote":
                await handle_cast_vote(lobby, username, msg_data)
            elif msg_type == "skip_discussion":
                await handle_skip_discussion(lobby, username)
            elif msg_type == "reset_game":
                await handle_reset_game(lobby, username)
            else:
                await send_to_player(
                    lobby,
                    username,
                    {"type": "error", "data": {"message": f"Unknown message type: {msg_type}"}},
                )
    except WebSocketDisconnect:
        remove_player(lobby, username)
        await broadcast_lobby_state(lobby)

        if lobby.game_state and lobby.game_state.phase != Phase.GAME_OVER:
            await broadcast(
                lobby,
                {
                    "type": "player_disconnected",
                    "data": {
                        "lobby_code": lobby.code,
                        "username": username,
                        "message": f"{username} disconnected from the game.",
                    },
                },
            )
