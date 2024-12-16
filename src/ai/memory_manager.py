from typing import List, Dict, Optional, TypedDict, Union
from datetime import datetime
import json
from enum import Enum

class MemoryType(Enum):
    CONVERSATION = "conversation"    # 대화 내용
    VOTE = "vote"                   # 투표 행위
    DEATH = "death"                 # 사망 정보
    INVESTIGATION = "investigation"  # 조사 결과 (경찰만)
    NIGHT_ACTION = "night_action"    # 밤 행동 결과
    OBSERVATION = "observation"      # 관찰한 행동/패턴

class GamePhase(Enum):
    DAY = "day"
    NIGHT = "night"

class Memory(TypedDict):
    """메모리 객체 인터페이스"""
    type: MemoryType           # 기억 유형
    content: str               # 내용
    turn: int                  # 게임 턴
    phase: GamePhase          # 게임 단계
    players: List[str]         # 관련 플레이어
    source: str               # 정보 출처
    timestamp: str            # 생성 시간 (자동 추가)

class MemoryManager:
    """메모리 관리자
    
    각 플레이어의 게임 진행 중 발생하는 정보와 경험을 관리합니다.
    PRD 요구사항:
    - 이전 턴의 정보 및 플레이어 행동 기록 저장
    - 각 플레이어는 본인의 기억에만 접근 가능
    
    주요 기능:
    1. 게임 정보 저장
    2. 대화 기록 저장
    3. 관련 기억 검색
    """
    def __init__(self, owner_id: str):
        self.owner_id = owner_id  # 이 메모리의 주인
        self.short_term_memory: List[Dict] = []
        self.long_term_memory: Dict[str, List[Dict]] = {
            memory_type.value: [] for memory_type in MemoryType
        }
        self.max_short_term_size = 50
        
    def add_memory(self, memory: Memory):
        """새로운 기억 추가
        
        Args:
            memory: Memory 타입의 기억 객체
                - type: 기억 유형 (대화/투표/사망 등)
                - content: 기억 내용
                - turn: 게임 턴
                - phase: 게임 단계 (낮/밤)
                - players: 관련된 플레이어 목록
                - source: 정보 출처 (direct_experience/conversation/public_announcement)
        """
        # 자신과 관련된 직접 경험이나 대화만 기억
        if not self._is_memorable(memory):
            return
            
        memory["timestamp"] = datetime.now().isoformat()
        
        self.short_term_memory.append(memory)
        
        # 단기 기억이 최대 크기를 초과하면 가장 오래된 기억 제거
        if len(self.short_term_memory) > self.max_short_term_size:
            self.short_term_memory.pop(0)
            
        # 장기 기억에 추가
        memory_type = memory["type"].value
        self.long_term_memory[memory_type].append(memory)
    
    def get_relevant_memories(self, 
                            context: str, 
                            phase: Optional[GamePhase] = None,
                            memory_type: Optional[MemoryType] = None,
                            limit: int = 10) -> List[Dict]:
        """컨텍스트 관련 기억 검색"""
        relevant_memories = []
        
        # 단기 기억에서 먼저 검색
        for memory in reversed(self.short_term_memory):
            if self._is_relevant(memory, context, phase, memory_type):
                relevant_memories.append(memory)
        
        for memories in self.long_term_memory.values():
            for memory in reversed(memories):
                if self._is_relevant(memory, context, phase, memory_type):
                    if memory not in relevant_memories:
                        relevant_memories.append(memory)
        
        return relevant_memories[:limit]

    def _is_relevant(self, 
                    memory: Dict, 
                    context: str, 
                    phase: Optional[GamePhase] = None,
                    memory_type: Optional[MemoryType] = None) -> bool:
        """기억의 관련성 확인"""
        if phase and memory.get("phase") != phase:
            return False
            
        if memory_type and memory.get("type") != memory_type:
            return False
            
        if context.lower() in memory["content"].lower():
            return True
            
        if "players" in memory and context in memory["players"]:
            return True
            
        return False
    
    def clear_short_term_memory(self):
        """단기 기억 초기화"""
        self.short_term_memory.clear()
        
    def save_memories(self, filepath: str):
        """기억을 파일로 저장"""
        memories = {
            "short_term": self.short_term_memory,
            "long_term": self.long_term_memory
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(memories, f, ensure_ascii=False, indent=2)
            
    def load_memories(self, filepath: str):
        """파일에서 기억 불러오기"""
        with open(filepath, 'r', encoding='utf-8') as f:
            memories = json.load(f)
            self.short_term_memory = memories["short_term"]
            self.long_term_memory = memories["long_term"]

    def get_recent_conversations(self, n: int = 5) -> List[Dict]:
        """최근 대화 내역 조회"""
        conversations = self.long_term_memory.get(MemoryType.CONVERSATION.value, [])
        return conversations[-n:] if conversations else []

    def _is_memorable(self, memory: Memory) -> bool:
        """이 정보를 기억해야 하는지 확인"""
        source = memory["source"]
        
        # 1. 직접 경험은 관련 플레이어만 기억
        if source == "direct_experience":
            return self.owner_id in memory["players"]
        
        # 2. 대화는 참여자만 기억
        if source == "conversation":
            return (self.owner_id in memory["players"] or 
                    memory["type"] == MemoryType.CONVERSATION)
        
        # 3. 공개 발표는 모든 플레이어가 기억
        if source == "public_announcement":
            return True
        
        return False