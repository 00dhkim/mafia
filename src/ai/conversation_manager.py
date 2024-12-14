from typing import List, Dict
from .llm_agent import LLMAgent

class ConversationManager:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.current_speaker = None
        
    async def generate_conversation(self, context: str, speaker: LLMAgent) -> str:
        """대화 생성"""
        pass
        
    def add_conversation(self, speaker: str, message: str):
        """대화 기록 추가"""
        pass
        
    def get_recent_conversations(self, n: int = 5) -> List[Dict]:
        """최근 대화 내역 조회"""
        pass 