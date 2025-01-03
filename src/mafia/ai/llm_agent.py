import random
import logging
import os

from openai import OpenAI
from typing import List, Dict, Optional

from mafia.ai import prompt_builder
from mafia.ai.memory_manager import MemoryManager
from mafia.utils.config import game_config
from mafia.utils.enum import ActionType, GamePhase, Role, ContextType
from mafia.utils.logger import GameLogger


class LLMAgent:
    """AI 플레이어 에이전트

    PRD 요구사항:
    - 독립적인 LLM 에이전트로 구현
    - 게임 상황 인식 및 의사결정 능력
    - 역할에 따른 적절한 행동 선택
    - 자연스러운 대화 생성 기능
    - 거짓말 탐지 및 수행 능력 (마피아 역할)

    주요 기능:
    1. 게임 상황 분석 및 의사결정
    2. 대화 생성 및 관리
    3. 역할별 특수 능력 사용
    4. 투표 결정
    """

    def __init__(self, player_id: int, memory_manager: MemoryManager, role: Role, name: str):
        assert isinstance(role, Role), "role must be an instance of Role"

        self.player_id = player_id
        self.role = role
        self.name = name
        self.memory_manager = memory_manager
        self.game_knowledge = {
            "known_roles": {},  # 확인된 다른 플레이어의 역할
            "suspicious_players": [],  # 의심스러운 플레이어 목록
            "trusted_players": [],  # 신뢰할 수 있는 플레이어 목록
        }
        # 전역 설정에서 AI 설정 가져오기
        self.ai_config = game_config.get_config("ai_settings")
        self.logger = logging.getLogger("mafia")

        self.llm_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def generate_response(self, context: ContextType) -> Dict:
        """
        LLM을 사용하여 응답 생성

        Args:
            context: 게임 상황 정보
        Returns:
            Dict: 생성된 응답
        """
        # 컨텍스트 구성
        if context.get("phase") == GamePhase.DAY_CONVERSATION:
            user_prompt, Schema = prompt_builder.day_conversation_prompt(
                context, self.game_knowledge
            )
        elif context.get("phase") == GamePhase.DAY_REASONING:
            user_prompt, Schema = prompt_builder.day_reasoning_prompt(context, self.game_knowledge)
        elif context.get("phase") == GamePhase.DAY_VOTE:
            user_prompt, Schema = prompt_builder.day_vote_prompt(context, self.game_knowledge)
        elif context.get("phase") == GamePhase.NIGHT_ACTION:
            user_prompt, Schema = prompt_builder.night_action_prompt(
                self.role, context, self.game_knowledge
            )
        else:
            raise ValueError(f"유효하지 않은 게임 페이즈입니다: {context.get('phase')}")

        # 시스템 메시지에 게임 규칙과 제약사항 추가
        developer_prompt = prompt_builder.developer_prompt(self.name, self.role)

        relevant_memories = self.memory_manager.get_recent_memories(
            current_day=context.get("day_count")
        )
        memories_prompt = "이전 기억:\n" + "\n".join(relevant_memories)

        messages = [
            {"role": "developer", "content": developer_prompt + user_prompt},
            {"role": "assistant", "content": memories_prompt},
        ]

        self.logger.info(messages)

        # LLM 호출
        # response = self.llm_client.chat.completions.create(
        #     model=self.ai_config["model"],
        #     messages=messages,
        #     temperature=self.ai_config["temperature"],
        #     max_tokens=self.ai_config["max_tokens"],
        #     presence_penalty=0.6,  # 반복 방지
        #     frequency_penalty=0.3,  # 다양성 유도
        # )
        completion = self.llm_client.beta.chat.completions.parse(
            model=self.ai_config["model"],
            messages=messages,
            response_format=Schema,
        )
        response = completion.choices[0].message
        if response.refusal:
            raise ValueError("LLM이 응답을 거부했습니다:", response.refusal)

        self.logger.info(repr(response.parsed))

        # 메모리 업데이트
        if context.get("phase") == GamePhase.DAY_CONVERSATION:
            type_ = "discuss"
        elif context.get("phase") == GamePhase.DAY_VOTE:
            type_ = "vote"
        elif context.get("phase") == GamePhase.NIGHT_ACTION:
            type_ = "skill"
        else:
            raise ValueError(f"유효하지 않은 게임 페이즈입니다: {context.get('phase')}")

        target = getattr(response.parsed, "target", None)
        content = getattr(response.parsed, "conversation", None)

        action = ActionType(
            type=type_,
            target=target,
            content=content,
        )
        self._update_memory(context, action)

        return str(response.parsed)  # FIXME:

    def _update_memory(self, context: ContextType, action: ActionType):
        """메모리 업데이트"""
        memory = {
            "phase": context.get("phase"),
            "day": context.get("day_count"),
            "action": action,
            "context": context,
        }
        self.memory_manager.add_memory(memory)

    def update_knowledge(self, new_information: Dict):
        # TODO:
        """게임 정보 업데이트"""
        if "role_reveal" in new_information:
            player = new_information["player"]
            role = new_information["role_reveal"]
            self.game_knowledge["known_roles"][player] = role

        if "suspicious" in new_information:
            player = new_information["player"]
            if player not in self.game_knowledge["suspicious_players"]:
                self.game_knowledge["suspicious_players"].append(player)

        if "trusted" in new_information:
            player = new_information["player"]
            if player not in self.game_knowledge["trusted_players"]:
                self.game_knowledge["trusted_players"].append(player)

    def _get_fallback_action(self, context: ContextType) -> Dict:
        """오류 발생 시 기본 행동 반환"""
        raise NotImplementedError


if __name__ == "__main__":
    from mafia.players.citizen import Citizen

    # 테스트 코드
    from dotenv import load_dotenv
    load_dotenv()

    # 로거 설정
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    memory_manager = MemoryManager(name="Alice")
    agent = LLMAgent(1, memory_manager, Role.MAFIA, "Alice")

    context = ContextType(
        day=1,
        phase=GamePhase.DAY_CONVERSATION,
        alive_players=[
            Citizen("Alice", 1, Role.CITIZEN),
            Citizen("Bob", 2, Role.CITIZEN),
            Citizen("Charlie", 3, Role.CITIZEN),
            Citizen("David", 4, Role.MAFIA),
        ],
        memories=[],
    )
    response = agent.generate_response(context)
    print(response)
