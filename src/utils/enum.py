from typing import TypedDict, List, Dict
from enum import Enum

names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Hannah", "Ivy", "Jack"]

class GamePhase(Enum):
    DAY_CONVERSATION = "낮 대화"
    DAY_REASONING = "낮 추리"
    DAY_VOTE = "낮 투표"
    NIGHT_ACTION = "밤 행동"

class Role(Enum):
    CITIZEN = "시민"
    DOCTOR = "의사"
    POLICE = "경찰"
    MAFIA = "마피아"

class Action(Enum):
    DISCUSS = "대화"
    VOTE = "투표"
    ACTION = "행동"

class MemoryType(TypedDict):
    """메모리 객체 타입"""
    day: int                  # 게임 턴
    phase: GamePhase          # 게임 단계
    speaker: str              # 발언자 (플레이어 및 시스템)
    content: str              # 내용

class GameStateType(TypedDict):
    """게임 상태 타입"""
    phase: GamePhase
    day_count: int
    alive_players: List[str]
    dead_players: List[str]
    vote_results: Dict[str, str]
    last_killed_player: str
    last_healed_player: str
    last_investigated_player: str

class ContextType(TypedDict):
    """컨텍스트 타입"""
    day_count: int
    phase: GamePhase
    alive_players: List[str]
    memories: List[MemoryType]

