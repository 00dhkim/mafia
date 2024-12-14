from typing import List, Dict
from .game_state import GameState
from .turn_manager import TurnManager
from ..players.base_player import BasePlayer
from ..players.citizen import Citizen
from ..players.doctor import Doctor
from ..players.police import Police
from ..players.mafia import Mafia
import random

class GameManager:
    def __init__(self):
        self.game_state = GameState()
        self.turn_manager = TurnManager(self.game_state)
    
    def initialize_game(self):
        """게임 초기화 및 역할 분배"""
        # 플레이어 생성
        players = [
            Citizen(f"시민{i}") for i in range(3)
        ] + [
            Doctor("의사"),
            Police("경찰"),
            Mafia("마피아1"),
            Mafia("마피아2")
        ]
        
        # 플레이어 순서 섞기
        random.shuffle(players)
        
        # 게임 상태 초기화
        self.game_state.alive_players = players
        self.game_state.dead_players = []
    
    async def run_game(self):
        """게임 메인 루프 실행"""
        while True:
            # 승리 조건 확인
            game_result = self.game_state.is_game_over()
            if game_result["is_over"]:
                print(f"게임 종료! 승리 팀: {game_result['winner']}")
                break
                
            # 낮 페이즈
            await self.turn_manager.run_day_phase()
            
            # 승리 조건 재확인
            game_result = self.game_state.is_game_over()
            if game_result["is_over"]:
                print(f"게임 종료! 승리 팀: {game_result['winner']}")
                break
                
            # 밤 페이즈
            await self.turn_manager.run_night_phase()
    
    def check_win_condition(self) -> bool:
        """승리 조건 확인"""
        pass 