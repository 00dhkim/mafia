import json
from typing import Dict
from pathlib import Path

class GameConfig:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'config'):
            self.config: Dict = {
                "roles": {
                    "mafia": 1,
                    "doctor": 1,
                    "police": 1,
                    "citizen": 1
                },
                "game_settings": {
                    "day_time_limit": 300,  # 낮 시간 제한 (초)
                    "night_time_limit": 60,  # 밤 시간 제한 (초)
                    "vote_time_limit": 60,   # 투표 시간 제한 (초)
                }
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
    
    def get_roles(self) -> Dict[str, int]:
        """역할 설정 조회"""
        return self.config.get("roles", {})