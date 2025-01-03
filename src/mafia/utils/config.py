import json
from typing import Dict
from pathlib import Path

class GameConfig:
    """게임 설정 관리자
    
    PRD 요구사항:
    - 게임 규칙 및 설정 관리
    - 역할별 인원수 설정
    - 시간 제한 설정
    
    주요 기능:
    1. 설정 파일 로드 및 관리
    2. 게임 규칙 설정 제공
    3. AI 설정 관리
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_initial_config()
        return cls._instance

    def _load_initial_config(self):
        """초기 설정 로드"""
        self.config: Dict = {
            "roles": {"mafia": 1, "doctor": 1, "police": 1, "citizen": 1},
            "game_settings": {
                "day_time_limit": 300,  # 낮 시간 제한 (초)
                "night_time_limit": 60,  # 밤 시간 제한 (초)
                "vote_time_limit": 60,  # 투표 시간 제한 (초)
            },
            "ai_settings": {"model": "gpt-4o-mini", "temperature": 0.7, "max_tokens": 150},
        }
        self.load_config()

    def load_config(self):
        """설정 파일 로드"""
        config_path = Path("config/game_config.json")
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
        except Exception as e:
            print(f"설정 파일 로드 실패: {e}")
            # 기본값 사용

    def get_config(self, key: str):
        """설정값 조회"""
        return self.config.get(key)

game_config = GameConfig()
