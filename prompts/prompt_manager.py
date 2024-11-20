from typing import List
from models.player import Player
from systems.chat_system import ChatMessage

class PromptManager:
    @staticmethod
    def get_discussion_prompt(player: Player, chat_history: List[ChatMessage]) -> str:
        print(f"\n프롬프트 생성 - 토론 ({player.name})")
        return f"""현재 게임 상황:
- 생존한 플레이어: {[p.name for p in player.game.players if p.is_alive]}
- 당신의 역할: {player.role.value}

채팅 기록:
{PromptManager._format_chat_history(chat_history)}

다음과 같이 대화에 참여하세요:
1. 자신의 역할을 적절히 숨기거나 드러내세요
2. 다른 플레이어들의 발언을 분석하세요
3. 승리를 위한 전략적 발언을 하세요

다음 발언을 작성하세요:"""

    @staticmethod
    def get_voting_prompt(player: Player, chat_history: List[ChatMessage]) -> str:
        print(f"\n프롬프트 생성 - 투표 ({player.name})")
        return f"""지금까지의 토론을 바탕으로 투표를 진행합니다.
가장 의심되는 플레이어를 지목하고 그 이유를 설명하세요.

채팅 기록:
{PromptManager._format_chat_history(chat_history)}

다음 형식으로 응답하세요:
투표 대상: [플레이어 이름]
이유: [상세한 설명]"""

    @staticmethod
    def get_police_action_prompt(player, chat_history: str) -> str:
        return f"""당신은 경찰({player.name})입니다. 채팅 기록을 바탕으로 조사할 대상을 선택하세요.
채팅 기록:
{chat_history}

다음 형식으로 응답하세요:
대상: [플레이어_이름]"""

    @staticmethod
    def get_mafia_action_prompt(player, chat_history: str) -> str:
        print(f"\n프롬프트 생성 - 마피아 행동 ({player.name})")
        return f"""당신은 마피아입니다. 채팅 기록을 바탕으로 제거할 대상을 선택하세요.
플레이어: {player.name}
채팅 기록:
{chat_history}

다음 형식으로 응답하세요:
대상: [플레이어_이름]"""

    @staticmethod
    def get_doctor_action_prompt(player, chat_history: str) -> str:
        return f"""당신은 의사입니다. 채팅 기록을 바탕으로 오늘 밤 누구를 보호할지 선택하세요.
현재 플레이어: {player.name}
채팅 기록:
{chat_history}

대상: [플레이어 이름]으로 답변해주세요."""

    @staticmethod
    def _format_chat_history(chat_history: List[ChatMessage]) -> str:
        return "\n".join([f"{msg.sender}: {msg.content}" for msg in chat_history])
  