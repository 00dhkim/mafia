from typing import List, Dict
from .game_state import GameState
from .turn_manager import TurnManager
from ..players.base_player import BasePlayer
from ..players.citizen import Citizen
from ..players.doctor import Doctor
from ..players.police import Police
from ..players.mafia import Mafia
from ..utils.config import GameConfig
import random

class GameManager:
    def __init__(self):
        self.game_state = GameState()
        self.turn_manager = TurnManager(self.game_state)
        self.config = GameConfig()
    
    def initialize_game(self):
        """게임 초기화 및 역할 분배"""
        # 설정에서 역할 정보 가져오기
        roles = self.config.get_roles()
        
        # 플레이어 생성
        players = []
        
        # 시민 생성
        for i in range(roles.get("citizen", 1)):
            players.append(Citizen(f"시민{i+1}"))
            
        # 의사 생성
        for i in range(roles.get("doctor", 1)):
            players.append(Doctor(f"의사{i+1}"))
            
        # 경찰 생성
        for i in range(roles.get("police", 1)):
            players.append(Police(f"경찰{i+1}"))
            
        # 마피아 생성
        for i in range(roles.get("mafia", 1)):
            players.append(Mafia(f"마피아{i+1}"))
        
        # 플레이어 순서 섞기
        random.shuffle(players)
        
        # 게임 상태 초기화
        self.game_state.alive_players = players
        self.game_state.dead_players = []
    
    def run_game(self):
        """게임 메인 루프 실행"""
        while True:
            # 승리 조건 확인
            game_result = self.game_state.is_game_over()
            if game_result["is_over"]:
                print(f"게임 종료! 승리 팀: {game_result['winner']}")
                break
                
            # 낮 페이즈
            self.turn_manager.run_day_phase()
            
            # 승리 조건 재확인
            game_result = self.game_state.is_game_over()
            if game_result["is_over"]:
                print(f"게임 종료! 승리 팀: {game_result['winner']}")
                break
                
            # 밤 페이즈
            self.turn_manager.run_night_phase()
    
    def check_win_condition(self) -> bool:
        """승리 조건 확인"""
        pass 