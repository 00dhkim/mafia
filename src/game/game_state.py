from typing import List, Dict, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..players.base_player import BasePlayer

class GamePhase(Enum):
    DAY = "day"
    NIGHT = "night"
    VOTING = "voting"

class GameState:
    def __init__(self):
        self.current_phase: GamePhase = GamePhase.DAY
        self.day_count: int = 1
        self.alive_players: List['BasePlayer'] = []
        self.dead_players: List['BasePlayer'] = []
        self.vote_results: Dict[str, str] = {}  # voter_name: voted_name
        self.last_killed_player: Optional['BasePlayer'] = None
        self.last_healed_player: Optional['BasePlayer'] = None
        self.last_investigated_player: Optional['BasePlayer'] = None
        
    def is_game_over(self) -> Dict[str, any]:
        """게임 종료 조건 확인"""
        mafia_count = sum(1 for p in self.alive_players if p.role == "마피아")
        citizen_count = sum(1 for p in self.alive_players if p.role != "마피아")
        
        if mafia_count == 0:
            return {"is_over": True, "winner": "시민"}
        if mafia_count >= citizen_count:
            return {"is_over": True, "winner": "마피아"}
        return {"is_over": False, "winner": None}

    def update_state(self, phase: GamePhase = None):
        """게임 상태 업데이트"""
        if phase:
            self.current_phase = phase
        if phase == GamePhase.DAY:
            self.day_count += 1
            self.vote_results.clear()
            self.last_killed_player = None
            self.last_healed_player = None
            self.last_investigated_player = None 