import pytest
from src.game.game_manager import GameManager, GamePhase
from src.players.base_player import BasePlayer
from src.players.mafia import Mafia
from src.players.doctor import Doctor
from src.players.police import Police
from src.players.citizen import Citizen

@pytest.fixture
def game_manager():
    manager = GameManager()
    manager.initialize_game()
    return manager

def test_game_initialization(game_manager):
    """게임 초기화 테스트"""
    assert game_manager.current_phase == GamePhase.DAY
    assert game_manager.day_count == 1
    assert len(game_manager.alive_players) > 0
    assert len(game_manager.dead_players) == 0

def test_phase_update(game_manager):
    """페이즈 변경 테스트"""
    game_manager.update_phase(GamePhase.NIGHT)
    assert game_manager.current_phase == GamePhase.NIGHT
    
    game_manager.update_phase(GamePhase.DAY)
    assert game_manager.current_phase == GamePhase.DAY
    assert game_manager.day_count == 2

def test_player_death(game_manager):
    """플레이어 사망 처리 테스트"""
    initial_alive_count = len(game_manager.alive_players)
    player = game_manager.alive_players[0]
    
    game_manager.handle_death(player)
    
    assert len(game_manager.alive_players) == initial_alive_count - 1
    assert len(game_manager.dead_players) == 1
    assert not player.is_alive

def test_voting_process(game_manager):
    """투표 처리 테스트"""
    game_manager.update_phase(GamePhase.VOTING)
    voter = game_manager.alive_players[0]
    target = game_manager.alive_players[1]
    
    game_manager.handle_vote(voter, target)
    assert target.name in game_manager.vote_results.values()

def test_night_action_mafia(game_manager):
    """마피아 밤 행동 테스트"""
    mafia = next(p for p in game_manager.alive_players if isinstance(p, Mafia))
    target = next(p for p in game_manager.alive_players if not isinstance(p, Mafia))
    
    action = {
        "type": "마피아",
        "target": target.name,
        "content": "공격"
    }
    
    game_manager.handle_night_action(mafia, action)
    assert game_manager.last_killed_player == target

def test_night_action_doctor(game_manager):
    """의사 밤 행동 테스트"""
    doctor = next(p for p in game_manager.alive_players if isinstance(p, Doctor))
    target = next(p for p in game_manager.alive_players if not isinstance(p, Doctor))
    
    action = {
        "type": "의사",
        "target": target.name,
        "content": "치료"
    }
    
    game_manager.handle_night_action(doctor, action)
    assert game_manager.last_healed_player == target

def test_game_over_conditions(game_manager):
    """게임 종료 조건 테스트"""
    # 시민 승리 케이스
    mafia = next(p for p in game_manager.alive_players if isinstance(p, Mafia))
    game_manager.handle_death(mafia)
    result = game_manager.is_game_over()
    assert result["is_over"]
    assert result["winner"] == "시민"

    # 마피아 승리 케이스
    game_manager = GameManager()  # 새 게임 시작
    game_manager.initialize_game()
    citizens = [p for p in game_manager.alive_players if not isinstance(p, Mafia)]
    for citizen in citizens[:-1]:  # 마피아와 시민 1명만 남김
        game_manager._handle_death(citizen)
    result = game_manager._is_game_over()
    assert result["is_over"]
    assert result["winner"] == "마피아"

def test_error_handling(game_manager):
    """에러 처리 테스트"""
    # 잘못된 플레이어 사망 처리
    with pytest.raises(Exception):
        game_manager.handle_death(None)
    
    # 잘못된 투표 대상
    voter = game_manager.alive_players[0]
    with pytest.raises(Exception):
        game_manager.handle_vote(voter, None)
    
    # 잘못된 밤 행동
    actor = game_manager.alive_players[0]
    with pytest.raises(Exception):
        game_manager.handle_night_action(actor, None) 
