import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.logic.game_engine import GameState, Phase
from app.logic.voting import Vote
from app.routes.lobby import lobby_players
from app.data.database import SessionLocal
from app.data.models import GameResult

router = APIRouter()
logger = logging.getLogger(__name__)


# Shared server state (single-lobby design)


# Track active WebSocket connections: username -> WebSocket
active_connections: dict[str, WebSocket] = {}

# Active game state – None when no game is running
game_state: GameState | None = None

# Discussion timer duration (seconds)
DISCUSSION_SECONDS = 90


# Helpers



async def broadcast(message: dict):
    """Send a JSON message to every connected player."""
    disconnected: list[str] = []
    for username, ws in active_connections.items():
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(username)
    for username in disconnected:
        active_connections.pop(username, None)


async def send_to_player(username: str, message: dict):
    """Send a private JSON message to one player."""
    ws = active_connections.get(username)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            active_connections.pop(username, None)


async def broadcast_lobby_state():
    """Tell every client who is currently in the lobby."""
    players = list(lobby_players)
    await broadcast({
        "type": "lobby_update",
        "data": {
            "players": players,
            "count": len(players),
            "can_start": len(players) >= 5,
        },
    })


def save_game_outcome(winner: str):
    """Persist the game result to MySQL."""
    db: Session = SessionLocal()
    try:
        result = GameResult(winner=winner)
        db.add(result)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to save game outcome")
    finally:
        db.close()



# Message handlers --- one function per client action



async def handle_start_game(username: str):
    """Host (or any player) starts the game once enough players have joined."""
    global game_state

    if game_state is not None and game_state.phase != Phase.GAME_OVER:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "A game is already in progress"},
        })
        return

    if len(lobby_players) < 5:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "Need at least 5 players to start"},
        })
        return

    # Create fresh game state from the current lobby
    game_state = GameState(list(lobby_players))
    start_info = game_state.start_game()

    # Send each player their own role + hand privately
    for pid in game_state.player_ids:
        role = start_info["roles"][pid]
        hand = game_state.get_hand(pid)

        private_msg: dict = {
            "type": "game_started",
            "data": {
                "role": role,
                "hand": hand,
                "players": game_state.player_ids,
            },
        }

        # Exploiters also learn who their teammates are
        if role == "exploiter":
            private_msg["data"]["exploiter_ids"] = start_info["exploiter_ids"]

        await send_to_player(pid, private_msg)

    # Broadcast the phase change so every client transitions
    await broadcast({
        "type": "phase_change",
        "data": {
            "phase": Phase.ROLE_REVEAL.value,
            "current_player": game_state.current_player,
            "turn_index": game_state.turn_index,
        },
    })

    # After a short delay, move to proposal phase
    await asyncio.sleep(5)
    if game_state and game_state.phase == Phase.ROLE_REVEAL:
        game_state.phase = Phase.PROPOSAL
        await broadcast({
            "type": "phase_change",
            "data": {
                "phase": Phase.PROPOSAL.value,
                "current_player": game_state.current_player,
                "turn_index": game_state.turn_index,
                "message": f"It is {game_state.current_player}'s turn to propose a policy.",
            },
        })


async def handle_propose_policy(username: str, data: dict):
    """The current player proposes a policy card from their hand."""
    global game_state

    if game_state is None:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "No game in progress"},
        })
        return

    if game_state.phase != Phase.PROPOSAL:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "Not in proposal phase"},
        })
        return

    if username != game_state.current_player:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "It is not your turn to propose"},
        })
        return

    card_index = data.get("card_index", -1)
    try:
        policy = game_state.propose_policy(username, card_index)
    except ValueError as e:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": str(e)},
        })
        return

    # Broadcast the proposed policy to all players
    await broadcast({
        "type": "policy_proposed",
        "data": {
            "proposed_by": username,
            "policy": {
                "name": policy.name,
                "description": policy.description,
                # NOTE: policy_type is NOT sent — players must debate and decide
            },
        },
    })

    # Move to discussion phase
    game_state.begin_discussion()
    await broadcast({
        "type": "phase_change",
        "data": {
            "phase": Phase.DISCUSSION.value,
            "message": f"{username} proposed: {policy.name}. Discuss! ({DISCUSSION_SECONDS}s)",
            "timer_seconds": DISCUSSION_SECONDS,
        },
    })

    # Auto-advance to voting after discussion timer
    asyncio.create_task(_discussion_timer())


async def _discussion_timer():
    """Wait for the discussion period then advance to voting."""
    await asyncio.sleep(DISCUSSION_SECONDS)
    if game_state and game_state.phase == Phase.DISCUSSION:
        await handle_begin_voting()


async def handle_begin_voting():
    """Transition from discussion to voting (can be triggered early or by timer)."""
    if game_state is None:
        return

    game_state.begin_voting()
    await broadcast({
        "type": "phase_change",
        "data": {
            "phase": Phase.VOTING.value,
            "message": "Voting is now open. Approve or reject the proposed policy.",
        },
    })


async def handle_cast_vote(username: str, data: dict):
    """A player casts their vote (approve / reject)."""
    global game_state

    if game_state is None:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "No game in progress"},
        })
        return

    if game_state.phase != Phase.VOTING:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "Not in voting phase"},
        })
        return

    if username in game_state.votes:
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "You have already voted this round"},
        })
        return

    vote_value = data.get("vote", "").lower()
    if vote_value not in ("approve", "reject"):
        await send_to_player(username, {
            "type": "error",
            "data": {"message": "Vote must be 'approve' or 'reject'"},
        })
        return

    vote = Vote.APPROVE if vote_value == "approve" else Vote.REJECT
    all_in = game_state.cast_vote(username, vote)

    # Acknowledge the vote privately
    await send_to_player(username, {
        "type": "vote_acknowledged",
        "data": {"vote": vote_value},
    })

    # Let everyone know how many votes are in (but not who voted what)
    await broadcast({
        "type": "vote_progress",
        "data": {
            "votes_cast": len(game_state.votes),
            "votes_needed": len(game_state.player_ids),
        },
    })

    # Once all votes are in, resolve the round
    if all_in:
        await _resolve_round()


async def _resolve_round():
    """Resolve the vote, broadcast accepted/rejected, check win condition."""
    global game_state

    if game_state is None:
        return

    result = game_state.resolve_round()
    approved = result["approved"]

    # Broadcast the resolution — accepted or rejected
    await broadcast({
        "type": "round_result",
        "data": {
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
    })

    # Check if game is over
    if result.get("winner"):
        winner = result["winner"]
        save_game_outcome(winner)

        await broadcast({
            "type": "game_over",
            "data": {
                "winner": winner,
                "summary": game_state.get_summary(),
                "message": (
                    "Reformers win! Sustainable policies prevailed."
                    if winner == "reformers"
                    else "Exploiters win! Exploitative policies dominated."
                ),
            },
        })
        return

    # Short pause then start next turn
    await asyncio.sleep(5)

    if game_state and game_state.phase != Phase.GAME_OVER:
        # Check if current player still has cards
        current = game_state.current_player
        hand = game_state.get_hand(current)

        if not hand:
            # No cards left — game ends in a draw
            await broadcast({
                "type": "game_over",
                "data": {
                    "winner": "draw",
                    "summary": game_state.get_summary(),
                    "message": "All policy cards have been played. Game ends in a draw.",
                },
            })
            save_game_outcome("draw")
            return

        game_state.phase = Phase.PROPOSAL
        await broadcast({
            "type": "phase_change",
            "data": {
                "phase": Phase.PROPOSAL.value,
                "current_player": game_state.current_player,
                "turn_index": game_state.turn_index,
                "message": f"It is {game_state.current_player}'s turn to propose a policy.",
            },
        })

        # Send updated hand to the current player
        await send_to_player(current, {
            "type": "hand_update",
            "data": {"hand": hand},
        })


async def handle_skip_discussion(username: str):
    """Allow early transition from discussion to voting."""
    if game_state and game_state.phase == Phase.DISCUSSION:
        await handle_begin_voting()


async def handle_reset_game(username: str):
    """Reset the server state so a new game can begin (moderator action)."""
    global game_state
    game_state = None
    lobby_players.clear()
    await broadcast({
        "type": "game_reset",
        "data": {"message": "Game has been reset. Return to lobby."},
    })



# Message router — maps incoming message types to handler functions


MESSAGE_HANDLERS = {
    "start_game": lambda u, d: handle_start_game(u),
    "propose_policy": handle_propose_policy,
    "cast_vote": handle_cast_vote,
    "skip_discussion": lambda u, d: handle_skip_discussion(u),
    "reset_game": lambda u, d: handle_reset_game(u),
}



# WebSocket endpoint



@router.websocket("/ws/{username}")
async def game_ws(websocket: WebSocket, username: str):
    await websocket.accept()
    active_connections[username] = websocket

    # Add to lobby if not already present (syncs with REST lobby)
    if username not in lobby_players:
        lobby_players.add(username)

    # Notify everyone about the updated lobby
    await broadcast_lobby_state()

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            msg_data = data.get("data", {})

            handler = MESSAGE_HANDLERS.get(msg_type)
            if handler:
                await handler(username, msg_data)
            else:
                await send_to_player(username, {
                    "type": "error",
                    "data": {"message": f"Unknown message type: {msg_type}"},
                })

    except WebSocketDisconnect:
        active_connections.pop(username, None)
        lobby_players.discard(username)
        await broadcast_lobby_state()

        # If a player disconnects during an active game, notify others
        if game_state and game_state.phase != Phase.GAME_OVER:
            await broadcast({
                "type": "player_disconnected",
                "data": {
                    "username": username,
                    "message": f"{username} disconnected from the game.",
                },
            })