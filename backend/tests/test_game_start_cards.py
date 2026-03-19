from app.logic.game_engine import GameState


def test_start_game_deals_cards_to_all_players():
    game_state = GameState(["alice", "bob", "charlie", "dave", "eve"])

    game_state.start_game()

    assert all(game_state.get_hand(player_id) for player_id in game_state.player_ids)


def test_start_game_deals_five_cards_per_player_with_five_players():
    game_state = GameState(["alice", "bob", "charlie", "dave", "eve"])

    game_state.start_game()

    assert all(len(game_state.get_hand(player_id)) == 5 for player_id in game_state.player_ids)
