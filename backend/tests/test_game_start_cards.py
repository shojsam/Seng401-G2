from app.logic.game_engine import GameState, Phase


def test_start_game_creates_shared_draw_pile():
    game_state = GameState(["alice", "bob", "charlie", "dave", "eve"])
    game_state.start_game()
    assert len(game_state.draw_pile) > 0


def test_start_game_assigns_roles_to_all_players():
    game_state = GameState(["alice", "bob", "charlie", "dave", "eve"])
    game_state.start_game()
    assert all(pid in game_state.roles for pid in game_state.player_ids)


def test_start_game_sets_phase_to_role_reveal():
    game_state = GameState(["alice", "bob", "charlie", "dave", "eve"])
    game_state.start_game()
    assert game_state.phase == Phase.ROLE_REVEAL
