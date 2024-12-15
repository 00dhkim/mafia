import pytest
from src.game.game_state import GameState, GamePhase
from src.game.turn_manager import TurnManager
from src.players.citizen import Citizen
from src.players.mafia import Mafia

@pytest.fixture
def game_setup():
    state = GameState()
    state.alive_players = [
        Citizen("시민1"),
        Citizen("시민2"),
        Mafia("마피아1")
    ]
    manager = TurnManager(state)
    return state, manager

def test_day_phase(game_setup):
    state, manager = game_setup
    
    manager.run_day_phase()
    assert state.current_phase == GamePhase.VOTING
    
    # 투표 결과 확인
    assert isinstance(state.vote_results, dict)

def test_night_phase(game_setup):
    state, manager = game_setup
    initial_alive_count = len(state.alive_players)
    
    manager.run_night_phase()
    assert state.current_phase == GamePhase.NIGHT

def test_handle_death(game_setup):
    state, manager = game_setup
    player = state.alive_players[0]
    initial_alive_count = len(state.alive_players)
    
    manager._handle_death(player)
    assert len(state.alive_players) == initial_alive_count - 1
    assert len(state.dead_players) == 1
    assert player in state.dead_players 