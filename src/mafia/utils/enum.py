from typing import Literal, TypedDict, List, Dict, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from mafia.players.base_player import BasePlayer

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


class ActionType(TypedDict):
    """액션 종류, 내용, 대상"""

    type: Literal["discuss", "vote", "skill"]
    target: "BasePlayer"
    content: str  # 대화 내용 or 선택의 이유

    def __repr__(self) -> str:
        return f"ActionType(type={self.type}, target={self.target}, content={self.content})"


class MemoryType(TypedDict):
    """메모리 객체 타입"""
    day: int                  # 게임 턴
    phase: GamePhase          # 게임 단계
    speaker: "BasePlayer"  # 발언자 (플레이어 및 사회자)
    content: str              # 내용

    def __repr__(self) -> str:
        return f"MemoryType(day={self.day}, phase={self.phase}, speaker={self.speaker}, content={self.content})"


class GameStateType(TypedDict):
    """게임 상태 타입"""
    day: int
    phase: GamePhase
    alive_players: List["BasePlayer"]
    dead_players: List["BasePlayer"]
    vote_results: Dict["BasePlayer", "BasePlayer"]

class ContextType(TypedDict):
    """컨텍스트 타입"""
    day: int
    phase: GamePhase
    alive_players: List["BasePlayer"]
    memories: List[MemoryType]
