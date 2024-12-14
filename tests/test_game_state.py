import pytest
from src.game.game_state import GameState, GamePhase
from src.players.citizen import Citizen
from src.players.mafia import Mafia

@pytest.fixture
def game_state():
    return GameState()

@pytest.fixture
def sample_players():
    return [
        Citizen("시민1"),
        Citizen("시민2"),
        Mafia("마피아1"),
        Mafia("마피아2")
    ]

def test_game_state_initialization(game_state):
    assert game_state.current_phase == GamePhase.DAY
    assert game_state.day_count == 1
    assert len(game_state.alive_players) == 0
    assert len(game_state.dead_players) == 0

def test_game_state_update(game_state):
    game_state.update_state(GamePhase.NIGHT)
    assert game_state.current_phase == GamePhase.NIGHT
    
    game_state.update_state(GamePhase.DAY)
    assert game_state.current_phase == GamePhase.DAY
    assert game_state.day_count == 2

def test_game_over_conditions(game_state, sample_players):
    # 초기 상태: 시민 2, 마피아 2
    game_state.alive_players = sample_players[:3]  # 시민 2, 마피아 1
    result = game_state.is_game_over()
    assert result["is_over"] == False
    
    # 마피아 전원 사망
    game_state.alive_players = [p for p in sample_players if p.role != "마피아"]
    result = game_state.is_game_over()
    assert result["is_over"] == True
    assert result["winner"] == "시민"
    
    # 마피아 수가 시민 수 이상
    game_state.alive_players = [p for p in sample_players if p.role == "마피아"]
    result = game_state.is_game_over()
    assert result["is_over"] == True
    assert result["winner"] == "마피아" 