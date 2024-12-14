from typing import List, Dict

class MemoryManager:
    def __init__(self):
        self.short_term_memory: List = []
        self.long_term_memory: Dict = {}
        
    def add_memory(self, memory: Dict):
        """새로운 기억 추가"""
        pass
    
    def get_relevant_memories(self, context: str) -> List[Dict]:
        """관련 기억 검색"""
        pass 