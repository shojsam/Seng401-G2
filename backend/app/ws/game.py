"""
ws/game.py — WebSocket handler for GREENWASHED (Leader/Vice variant).

Message types the frontend can send:
  start_game        → kicks off role assignment + deck creation
  nominate_vice     → { "vice_id": "<player>" }
  cast_vote         → { "vote": "approve" | "reject" }
  leader_discard    → { "discard_index": 0|1|2 }
  vice_enact        → { "enact_index": 0|1 }
  next_round_ready  → player is ready to proceed after policy enacted
  reset_game        → resets lobby to pre-game state

Message types the backend broadcasts / sends:
  lobby_update, game_started, phase_change, nomination,
  vote_acknowledged, vote_progress, election_result,
  leader_hand (private), vice_hand (private),
  round_result, next_round_progress, game_over,
  player_disconnected, error
"""
import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..data.models import save_game_result
from ..logic.game_engine import GameState, Phase
from ..logic.voting import Vote
from ..state.lobbies import (
    LobbyState,
    get_lobby,
    normalize_lobby_code,
    remove_player,
    reset_lobby,
)

router = APIRouter()
logger = logging.getLogger(__name__)

ROLE_REVEAL_SECONDS = 5


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def broadcast(lobby: LobbyState, message: dict):
    disconnected: list[str] = []
    for username, ws in lobby.active_connections.items():
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(username)
    for username in disconnected:
        remove_player(lobby, username)


async def broadcast_lobby_state(lobby: LobbyState):
    await broadcast(lobby, {
        "type": "lobby_update",
        "data": {
            "lobby_code": lobby.code,
            "players": list(lobby.players),
        },
    })


async def send_to_player(lobby: LobbyState, username: str, message: dict):
    ws = lobby.active_connections.get(username)
    if ws:
        try:
            await ws.send_json(message)
        except Exception:
            pass


# ------------------------------------------------------------------
# Handler: start_game
# ------------------------------------------------------------------

async def handle_start_game(lobby: LobbyState, username: str):
    if lobby.game_state is not None:
        await send_to_player(lobby, username, {
            "type": "error",
            "data": {"message": "A game is already in progress"},
        })
        return

    if len(lobby.players) < 5:
        await send_to_player(lobby, username, {
            "type": "error",
            "data": {"message": "Need at least 5 players to start"},
        })
        return

    lobby.ready_players.clear()
    lobby.game_state = GameState(list(lobby.players))
    gs = lobby.game_state
    start_info = gs.start_game()

    # Send each player their private role (exploiters also see each other)
    for pid in gs.player_ids:
        role = start_info["roles"][pid]
        private_msg: dict = {
            "type": "game_started",
            "data": {
                "lobby_code": lobby.code,
                "role": role,
                "players": gs.player_ids,
                "leader": start_info["leader"],
                "draw_pile_remaining": len(gs.draw_pile),
            },
        }
        if role == "exploiter":
            private_msg["data"]["exploiter_ids"] = start_info["exploiter_ids"]
        await send_to_player(lobby, pid, private_msg)

    # Broadcast role reveal phase
    await broadcast(lobby, {
        "type": "phase_change",
        "data": {
            "lobby_code": lobby.code,
            "phase": Phase.ROLE_REVEAL.value,
            "leader": gs.leader,
            "turn_index": gs.turn_index,
        },
    })

    # Initialize role acknowledgment tracking (wait for all players to press OKAY)
    if not hasattr(lobby, "role_acks"):
        lobby.role_acks = set()  # type: ignore[attr-defined]
    else:
        lobby.role_acks.clear()  # type: ignore[attr-defined]


# ------------------------------------------------------------------
# Handler: role_acknowledged
# ------------------------------------------------------------------

async def handle_role_acknowledged(lobby: LobbyState, username: str):
    gs = lobby.game_state
    if gs is None or gs.phase != Phase.ROLE_REVEAL:
        return

    if not hasattr(lobby, "role_acks"):
        lobby.role_acks = set()  # type: ignore[attr-defined]

    lobby.role_acks.add(username)  # type: ignore[attr-defined]
    acked = len(lobby.role_acks)  # type: ignore[attr-defined]
    total = len(gs.player_ids)

    # Broadcast progress to all players
    await broadcast(lobby, {
        "type": "role_ack_progress",
        "data": {
            "lobby_code": lobby.code,
            "acknowledged": acked,
            "total": total,
            "message": f"Waiting for players... {acked}/{total} ready",
        },
    })

    # When all players have acknowledged, move to nomination
    if acked >= total:
        gs.phase = Phase.NOMINATION
        await _broadcast_nomination_phase(lobby)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

async def _broadcast_nomination_phase(lobby: LobbyState):
    gs = lobby.game_state
    if gs is None:
        return
    await broadcast(lobby, {
        "type": "phase_change",
        "data": {
            "lobby_code": lobby.code,
            "phase": Phase.NOMINATION.value,
            "leader": gs.leader,
            "turn_index": gs.turn_index,
            "sustainable_count": gs.enacted_sustainable,
            "exploiter_count": gs.enacted_exploiter,
            "election_tracker": gs.election_tracker,
            "ineligible_ids": gs.ineligible_for_vice,
            "message": f"It is {gs.leader}'s turn to nominate a Vice.",
        },
    })


# ------------------------------------------------------------------
# Handler: nominate_vice
# ------------------------------------------------------------------

async def handle_nominate_vice(lobby: LobbyState, username: str, data: dict):
    gs = lobby.game_state
    if gs is None:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "No game in progress"},
        })
        return

    if gs.phase != Phase.NOMINATION:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "Not in nomination phase"},
        })
        return

    vice_id = str(data.get("vice_id", "")).strip()
    if not vice_id:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "vice_id is required"},
        })
        return

    try:
        result = gs.nominate_vice(username, vice_id)
    except ValueError as exc:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": str(exc)},
        })
        return

    await broadcast(lobby, {
        "type": "nomination",
        "data": {
            "lobby_code": lobby.code,
            "leader": result["leader"],
            "nominated_vice": result["nominated_vice"],
            "message": f"{result['leader']} nominated {result['nominated_vice']} as Vice.",
        },
    })

    await broadcast(lobby, {
        "type": "phase_change",
        "data": {
            "lobby_code": lobby.code,
            "phase": Phase.ELECTION.value,
            "leader": result["leader"],
            "nominated_vice": result["nominated_vice"],
            "message": "Vote to approve or reject this Leader/Vice pair.",
        },
    })


# ------------------------------------------------------------------
# Handler: cast_vote (election)
# ------------------------------------------------------------------

async def handle_cast_vote(lobby: LobbyState, username: str, data: dict):
    gs = lobby.game_state
    if gs is None:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "No game in progress"},
        })
        return

    if gs.phase != Phase.ELECTION:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "Not in election phase"},
        })
        return

    if username in gs.votes:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "You have already voted this round"},
        })
        return

    vote_value = str(data.get("vote", "")).lower()
    if vote_value not in ("approve", "reject"):
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "Vote must be 'approve' or 'reject'"},
        })
        return

    vote = Vote.APPROVE if vote_value == "approve" else Vote.REJECT
    all_in = gs.cast_vote(username, vote)

    await send_to_player(lobby, username, {
        "type": "vote_acknowledged", "data": {"vote": vote_value},
    })
    await broadcast(lobby, {
        "type": "vote_progress",
        "data": {
            "lobby_code": lobby.code,
            "votes_cast": len(gs.votes),
            "votes_needed": len(gs.player_ids),
        },
    })

    if all_in:
        await _resolve_election(lobby)


async def _resolve_election(lobby: LobbyState):
    gs = lobby.game_state
    if gs is None:
        return

    result = gs.resolve_election()
    approved = result["approved"]

    await broadcast(lobby, {
        "type": "election_result",
        "data": {
            "lobby_code": lobby.code,
            "approved": approved,
            "votes": result["votes"],
            "leader": result["leader"],
            "nominated_vice": result["nominated_vice"],
            "election_tracker": gs.election_tracker,
            "message": (
                f"Election PASSED — {result['leader']} and {result['nominated_vice']} govern this round."
                if approved
                else f"Election FAILED ({gs.election_tracker}/3). Leadership rotates."
            ),
        },
    })

    if approved:
        # Send the 3-card hand privately to the leader
        await send_to_player(lobby, result["leader"], {
            "type": "leader_hand",
            "data": {
                "cards": result.get("leader_hand", []),
                "message": "You drew 3 policy cards. Discard 1 and pass the remaining 2 to your Vice.",
            },
        })
        await broadcast(lobby, {
            "type": "phase_change",
            "data": {
                "lobby_code": lobby.code,
                "phase": Phase.LEADER_DISCARD.value,
                "leader": result["leader"],
                "nominated_vice": result["nominated_vice"],
                "message": f"{result['leader']} is reviewing policy cards...",
            },
        })
    else:
        # Check if forced enactment happened
        if "forced_policy" in result:
            forced = result["forced_policy"]
            await broadcast(lobby, {
                "type": "round_result",
                "data": {
                    "lobby_code": lobby.code,
                    "enacted_policy": forced["enacted_policy"],
                    "sustainable_count": forced["sustainable_count"],
                    "exploiter_count": forced["exploiter_count"],
                    "draw_pile_remaining": len(gs.draw_pile),
                    "message": "3 failed elections! A policy was enacted automatically.",
                },
            })
            if forced.get("winner"):
                await _handle_game_over(lobby, forced["winner"])
                return

            # Initialize next round ready tracking
            _init_next_round_acks(lobby)

        # If no forced enactment and no game over, move to next nomination
        elif gs.phase != Phase.GAME_OVER:
            await _broadcast_nomination_phase(lobby)


# ------------------------------------------------------------------
# Handler: leader_discard
# ------------------------------------------------------------------

async def handle_leader_discard(lobby: LobbyState, username: str, data: dict):
    gs = lobby.game_state
    if gs is None:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "No game in progress"},
        })
        return

    if gs.phase != Phase.LEADER_DISCARD:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "Not in leader discard phase"},
        })
        return

    discard_index = data.get("discard_index", -1)
    if not isinstance(discard_index, int):
        discard_index = -1

    try:
        result = gs.leader_discard(username, discard_index)
    except ValueError as exc:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": str(exc)},
        })
        return

    vice_id = result["vice_id"]

    # Send the 2 remaining cards privately to the vice
    await send_to_player(lobby, vice_id, {
        "type": "vice_hand",
        "data": {
            "cards": result["vice_hand"],
            "message": "Choose 1 policy to enact. The other will be discarded.",
        },
    })

    await broadcast(lobby, {
        "type": "phase_change",
        "data": {
            "lobby_code": lobby.code,
            "phase": Phase.VICE_ENACT.value,
            "leader": gs.leader,
            "nominated_vice": vice_id,
            "message": f"{vice_id} is choosing which policy to enact...",
        },
    })


# ------------------------------------------------------------------
# Handler: vice_enact
# ------------------------------------------------------------------

async def handle_vice_enact(lobby: LobbyState, username: str, data: dict):
    gs = lobby.game_state
    if gs is None:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "No game in progress"},
        })
        return

    if gs.phase != Phase.VICE_ENACT:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": "Not in vice enact phase"},
        })
        return

    enact_index = data.get("enact_index", -1)
    if not isinstance(enact_index, int):
        enact_index = -1

    try:
        result = gs.vice_enact(username, enact_index)
    except ValueError as exc:
        await send_to_player(lobby, username, {
            "type": "error", "data": {"message": str(exc)},
        })
        return

    await broadcast(lobby, {
        "type": "round_result",
        "data": {
            "lobby_code": lobby.code,
            "enacted_policy": result["enacted_policy"],
            "sustainable_count": result["sustainable_count"],
            "exploiter_count": result["exploiter_count"],
            "draw_pile_remaining": len(gs.draw_pile),
            "message": f"Policy enacted: {result['enacted_policy']['title']} ({result['enacted_policy']['policy_type']})",
        },
    })

    if result.get("winner"):
        await _handle_game_over(lobby, result["winner"])
    elif gs.phase == Phase.NOMINATION:
        # Instead of auto-advancing, wait for all players to press "Next Round"
        _init_next_round_acks(lobby)


# ------------------------------------------------------------------
# Handler: next_round_ready
# ------------------------------------------------------------------

def _init_next_round_acks(lobby: LobbyState):
    """Initialize the next-round acknowledgment tracker."""
    if not hasattr(lobby, "next_round_acks"):
        lobby.next_round_acks = set()  # type: ignore[attr-defined]
    else:
        lobby.next_round_acks.clear()  # type: ignore[attr-defined]


async def handle_next_round_ready(lobby: LobbyState, username: str):
    gs = lobby.game_state
    if gs is None or gs.phase != Phase.NOMINATION:
        return

    if not hasattr(lobby, "next_round_acks"):
        lobby.next_round_acks = set()  # type: ignore[attr-defined]

    lobby.next_round_acks.add(username)  # type: ignore[attr-defined]
    ready = len(lobby.next_round_acks)  # type: ignore[attr-defined]
    total = len(gs.player_ids)

    # Broadcast progress to all players
    await broadcast(lobby, {
        "type": "next_round_progress",
        "data": {
            "lobby_code": lobby.code,
            "ready": ready,
            "total": total,
        },
    })

    # When all players are ready, proceed to nomination
    if ready >= total:
        await _broadcast_nomination_phase(lobby)


# ------------------------------------------------------------------
# Handler: reset_game
# ------------------------------------------------------------------

async def handle_reset_game(lobby: LobbyState, _username: str):
    reset_lobby(lobby)
    await broadcast(lobby, {
        "type": "game_reset",
        "data": {
            "lobby_code": lobby.code,
            "message": "Game has been reset. Return to lobby.",
        },
    })


# ------------------------------------------------------------------
# Handler: character_selected
# ------------------------------------------------------------------

async def handle_character_selected(lobby: LobbyState, username: str, data: dict):
    character_id = data.get("character_id", 0)
    if not isinstance(character_id, int) or character_id <= 0:
        return

    # Store character selection on the lobby
    if not hasattr(lobby, "character_selections"):
        lobby.character_selections = {}  # type: ignore[attr-defined]
    lobby.character_selections[username] = character_id  # type: ignore[attr-defined]

    # Broadcast character update to all players
    await broadcast(lobby, {
        "type": "character_update",
        "data": {
            "lobby_code": lobby.code,
            "username": username,
            "character_id": character_id,
        },
    })

    # Broadcast progress
    total_selected = len(lobby.character_selections)  # type: ignore[attr-defined]
    total_players = len(lobby.players)
    await broadcast(lobby, {
        "type": "character_progress",
        "data": {
            "lobby_code": lobby.code,
            "selected": total_selected,
            "total": total_players,
            "message": f"Character selected: {total_selected}/{total_players} ready",
        },
    })

    # Auto-start when 5+ players and all have chosen
    if total_players >= 5 and total_selected >= total_players:
        gs = lobby.game_state
        if gs is None or gs.phase == Phase.GAME_OVER:
            await _auto_start_game(lobby)


async def _auto_start_game(lobby: LobbyState):
    """Start the game automatically once all players have selected characters."""
    lobby.ready_players.clear()
    lobby.game_state = GameState(list(lobby.players))
    gs = lobby.game_state
    start_info = gs.start_game()

    for pid in gs.player_ids:
        role = start_info["roles"][pid]
        private_msg: dict = {
            "type": "game_started",
            "data": {
                "lobby_code": lobby.code,
                "role": role,
                "players": gs.player_ids,
                "leader": start_info["leader"],
                "draw_pile_remaining": len(gs.draw_pile),
            },
        }
        if role == "exploiter":
            private_msg["data"]["exploiter_ids"] = start_info["exploiter_ids"]
        await send_to_player(lobby, pid, private_msg)

    await broadcast(lobby, {
        "type": "phase_change",
        "data": {
            "lobby_code": lobby.code,
            "phase": Phase.ROLE_REVEAL.value,
            "leader": gs.leader,
            "turn_index": gs.turn_index,
        },
    })

    if not hasattr(lobby, "role_acks"):
        lobby.role_acks = set()  # type: ignore[attr-defined]
    else:
        lobby.role_acks.clear()  # type: ignore[attr-defined]


# ------------------------------------------------------------------
# Game over
# ------------------------------------------------------------------

async def _handle_game_over(lobby: LobbyState, winner: str):
    gs = lobby.game_state
    if gs is None:
        return

    try:
        save_game_result(winner)
    except Exception as exc:
        logger.warning("Failed to save game result: %s", exc)

    summary = gs.get_summary()

    # Include character selections so every client has the full picture
    char_selections = getattr(lobby, "character_selections", {})

    await broadcast(lobby, {
        "type": "game_over",
        "data": {
            "lobby_code": lobby.code,
            "winner": winner,
            "summary": summary,
            "players": gs.player_ids,
            "character_selections": char_selections,
            "message": (
                "Reformers win! Sustainable policies prevailed."
                if winner == "reformers"
                else "Exploiters win! Exploitative policies dominated."
            ),
        },
    })


# ------------------------------------------------------------------
# WebSocket endpoint
# ------------------------------------------------------------------

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

    # Send existing character selections to the newly connected player
    char_selections = getattr(lobby, "character_selections", {})
    if char_selections:
        for player_name, char_id in char_selections.items():
            await send_to_player(lobby, username, {
                "type": "character_update",
                "data": {
                    "lobby_code": lobby.code,
                    "username": player_name,
                    "character_id": char_id,
                },
            })

    try:
        while True:
            raw = await websocket.receive_json()
            msg_type = raw.get("type", "")
            msg_data = raw.get("data", {})

            if msg_type == "start_game":
                await handle_start_game(lobby, username)
            elif msg_type == "nominate_vice":
                await handle_nominate_vice(lobby, username, msg_data)
            elif msg_type == "cast_vote":
                await handle_cast_vote(lobby, username, msg_data)
            elif msg_type == "leader_discard":
                await handle_leader_discard(lobby, username, msg_data)
            elif msg_type == "vice_enact":
                await handle_vice_enact(lobby, username, msg_data)
            elif msg_type == "next_round_ready":
                await handle_next_round_ready(lobby, username)
            elif msg_type == "reset_game":
                await handle_reset_game(lobby, username)
            elif msg_type == "character_selected":
                await handle_character_selected(lobby, username, msg_data)
            elif msg_type == "role_acknowledged":
                await handle_role_acknowledged(lobby, username)
            else:
                await send_to_player(lobby, username, {
                    "type": "error",
                    "data": {"message": f"Unknown message type: {msg_type}"},
                })
    except WebSocketDisconnect:
        remove_player(lobby, username)
        await broadcast_lobby_state(lobby)

        if lobby.game_state and lobby.game_state.phase != Phase.GAME_OVER:
            lobby.game_state.phase = Phase.GAME_OVER
            lobby.game_state.winner = None
            await broadcast(lobby, {
                "type": "game_over",
                "data": {
                    "lobby_code": lobby.code,
                    "winner": "none",
                    "disconnected_player": username,
                    "summary": lobby.game_state.get_summary(),
                    "players": lobby.game_state.player_ids,
                    "character_selections": getattr(lobby, "character_selections", {}),
                    "message": f"{username} disconnected. Game ended.",
                },
            })