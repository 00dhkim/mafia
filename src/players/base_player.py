from abc import ABC, abstractmethod
from ..ai.llm_agent import LLMAgent
from ..ai.memory_manager import MemoryManager
from typing import Dict, Optional, List, TypeVar, Callable
import random
import logging

T = TypeVar('T')

class BasePlayer(ABC):
    """플레이어 기본 클래스
    
    PRD 요구사항:
    - 각 역할별 특수 능력 구현
    - AI 에이전트와의 연동
    - 개별 메모리 관리
    
    주요 기능:
    1. 기본 플레이어 상태 관리 (생존 여부 등)
    2. AI 에이전트를 통한 의사결정
    3. 행동 검증 및 실행
    4. 대화 및 투표 참여
    """
    def __init__(self, name: str):
        self.name = name
        self.is_alive = True
        self.is_healed = False
        self.role = None
        self.memory_manager = MemoryManager(owner_id=name)
        self.ai_agent = LLMAgent(
            player_id=name, 
            memory_manager=self.memory_manager,
            role=self.role
        )
        self.logger = logging.getLogger(__name__)

    def _validate_and_get_target(
        self,
        target_name: str,
        candidates: List[T],
        name_selector: Callable[[T], str],
        exclude_self: bool = True
    ) -> Optional[T]:
        """
        AI 응답을 검증하고 유효한 대상을 반환
        
        Args:
            target_name: AI가 선택한 대상의 이름
            candidates: 선택 가능한 대상 목록
            name_selector: 대상에서 이름을 추출하는 함수
            exclude_self: 자기 자신을 제외할지 여부
            
        Returns:
            선택된 대상 또는 None
        """
        if not candidates:
            return None
            
        # 자기 자신 제외
        if exclude_self:
            candidates = [c for c in candidates if name_selector(c) != self.name]
            
        # 유효한 대상 찾기
        for candidate in candidates:
            if name_selector(candidate) in target_name:
                return candidate
                
        # 유효하지 않은 경우 경고 로그 출력 후 랜덤 선택
        self.logger.warning(
            f"[{self.role}] 유효하지 않은 대상 선택: {target_name}. "
            f"가능한 대상: {[name_selector(c) for c in candidates]}"
        )
        return random.choice(candidates) if candidates else None

    @abstractmethod
    def take_action(self, game_state: 'GameState') -> Dict:
        """
        게임 상태를 기반으로 플레이어의 행동을 결정하고 수행
        
        Args:
            game_state (GameState): 현재 게임 상태 정보
            
        Returns:
            Dict: 수행한 행동의 결과
        """
        raise NotImplementedError

    def discuss(self, game_state: 'GameState') -> Dict:
        """낮 페이즈 대화 수행"""
        context = self.memory_manager.get_relevant_memories(game_state)
        message = self.ai_agent.generate_response(context)
        
        result = {
            "success": True,
            "message": message
        }
        
        self.memory_manager.add_memory({
            "action": "discuss",
            "message": message,
            "turn": game_state.day_count
        })
        
        return result

    def vote(self, candidates) -> str:
        """투표 진행"""
        if not candidates:
            return ""
            
        context = {
            "role": self.role,
            "phase": "투표",
            "alive_players": [p.name for p in candidates],
            "memories": self.memory_manager.get_relevant_memories(None)
        }
        
        vote_target = self.ai_agent.generate_response(context)
        
        # 유효한 투표 대상 확인
        for candidate in candidates:
            if candidate.name in vote_target:
                return candidate.name
                
        # 유효하지 않은 경우 랜덤 선택
        import random
        return random.choice(candidates).name

    def receive_public_info(self, info: Memory):
        """공개 정보 수신 및 저장"""
        self.memory_manager.add_memory(info)