import pytest
from src.game.game_state import GameState, GamePhase
from src.players.mafia import Mafia
from src.players.doctor import Doctor
from src.players.police import Police
from src.players.citizen import Citizen

@pytest.fixture
def game_state():
    state = GameState()
    state.current_phase = GamePhase.NIGHT
    return state

@pytest.fixture
def players():
    return {
        "mafia": Mafia("마피아1"),
        "doctor": Doctor("의사1"),
        "police": Police("경찰1"),
        "citizen": Citizen("시민1")
    }

@pytest.mark.asyncio
async def test_mafia_kill_action(game_state, players):
    mafia = players["mafia"]
    target = players["citizen"]
    
    # 살해 시도
    result = mafia._kill(target)
    assert result["success"] == True
    assert target.is_alive == False
    
    # 이미 죽은 대상 살해 시도
    result = mafia._kill(target)
    assert result["success"] == False

@pytest.mark.asyncio
async def test_doctor_heal_action(game_state, players):
    doctor = players["doctor"]
    target = players["citizen"]
    
    # 치료
    result = doctor._heal(target)
    assert result["success"] == True
    assert target.is_healed == True

@pytest.mark.asyncio
async def test_police_investigate_action(game_state, players):
    police = players["police"]
    target = players["mafia"]
    
    # 조사
    result = police._investigate(target)
    assert result["success"] == True
    assert "마피아" in result["message"]

@pytest.mark.asyncio
async def test_night_phase_restrictions(game_state, players):
    game_state.current_phase = GamePhase.DAY
    
    # 낮에는 특수 능력 사용 불가
    result = await players["mafia"].take_action(game_state)
    assert result["success"] == False
    assert "밤이 아닙니다" in result["message"] 