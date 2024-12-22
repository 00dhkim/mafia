"""
TODO: 로깅은 각 LLM마다 입출력에 대해 저장, 전체 로그도 저장
"""

import logging
from typing import Any

class GameLogger:
    """게임 로깅 관리자
    
    PRD 요구사항:
    - 게임 진행 상황 기록
    - 디버깅 및 분석을 위한 로그 관리
    
    주요 기능:
    1. 게임 상태 로깅
    2. 플레이어 행동 로깅
    3. AI 응답 로깅
    4. 에러 및 경고 로깅
    """
    def __init__(self):
        self.logger = logging.getLogger("mafia_game")
        self._setup_logger()
        
    def _setup_logger(self):
        """로거 설정"""
        pass
        
    def log_game_state(self, state: Any):
        """게임 상태 로깅"""
        pass
        
    def log_player_action(self, player: str, action: str):
        """플레이어 행동 로깅"""
        pass 

game_logger = GameLogger()