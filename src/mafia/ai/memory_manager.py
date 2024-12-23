from typing import List
from mafia.utils.enum import MemoryType


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

    def __init__(self, player_id: str):
        self.player_id = player_id  # 이 메모리의 주인
        self.memories: List[MemoryType] = []

    def add_memory(self, memory: MemoryType):
        """새로운 기억 추가

        Args:
            memory: Memory 타입의 기억 객체
                - day: 게임 턴
                - phase: 게임 단계 (낮/밤)
                - speaker: 발언자
                - content: 내용
        """
        self.memories.append(memory)

        return True

    def get_recent_memories(self, current_day: int, days: int = 3) -> List[MemoryType]:
        """
        최근 기억 조회
        Args:
            days: 최근 기억 조회 일 수
            current_day: 현재 게임 턴
        """
        return [memory for memory in self.memories if memory["day"] >= current_day - days]

    def get_all_memories(self) -> List[MemoryType]:
        """모든 기억 조회"""
        return self.memories

    def clear_memories(self):
        """모든 기억 삭제"""
        self.memories = []
        return True
