import json
from typing import Dict

class GameConfig:
    def __init__(self):
        self.config: Dict = {}
        self.load_config()
        
    def load_config(self):
        """설정 파일 로드"""
        pass
        
    def get_config(self, key: str):
        """설정값 조회"""
        pass 