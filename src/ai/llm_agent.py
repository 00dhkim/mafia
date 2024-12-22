from typing import List, Dict, Optional
import openai

from ai import prompt_builder
from .memory_manager import MemoryManager
import random
from utils.config import game_config
from utils.enum import GamePhase, Role, Action, ContextType


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
    def __init__(self, player_id: int, memory_manager: MemoryManager, role: Role):
        assert isinstance(role, Role), "role must be an instance of Role"

        self.player_id = player_id
        self.role = role
        self.memory_manager = memory_manager
        self.game_knowledge = {
            "known_roles": {},  # 확인된 다른 플레이어의 역할
            "suspicious_players": [],  # 의심스러운 플레이어 목록
            "trusted_players": [],  # 신뢰할 수 있는 플레이어 목록
        }
        # 전역 설정에서 AI 설정 가져오기
        self.ai_config = game_config.get_config("ai_settings")

    def generate_response(self, context: ContextType) -> Dict:
        """
        LLM을 사용하여 응답 생성

        Args:
            context: 게임 상황 정보
        Returns:
            Dict: 생성된 응답
        """
        try:
            # 컨텍스트 구성
            if context.get("phase") == GamePhase.DAY_CONVERSATION:
                user_prompt = prompt_builder.day_conversation_prompt(context, self.game_knowledge)
            elif context.get("phase") == GamePhase.DAY_REASONING:
                user_prompt = prompt_builder.day_reasoning_prompt(context, self.game_knowledge)
            elif context.get("phase") == GamePhase.DAY_VOTE:
                user_prompt = prompt_builder.day_vote_prompt(context, self.game_knowledge)
            elif context.get("phase") == GamePhase.NIGHT_ACTION:
                user_prompt = prompt_builder.night_action_prompt(context, self.game_knowledge)

            relevant_memories = self.memory_manager.get_recent_memories(
                days=3, current_day=context.get("day_count")
            )

            # 시스템 메시지에 게임 규칙과 제약사항 추가
            system_prompt = prompt_builder.system_prompt(self.role)

            relevant_memories = self.memory_manager.get_recent_memories(
                days=3, current_day=context.get("day_count")
            )
            memories_prompt = "이전 기억:\n" + "\n".join(relevant_memories)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": memories_prompt} #TODO: openai API의 구조에 맞게 messages 구성했는지 확인
            ]

            # LLM 호출
            try:
                response = openai.ChatCompletion.create(
                    model=self.ai_config["model"],
                    messages=messages,
                    temperature=self.ai_config["temperature"],
                    max_tokens=self.ai_config["max_tokens"],
                    presence_penalty=0.6,  # 반복 방지
                    frequency_penalty=0.3   # 다양성 유도
                )
            except Exception as e:
                raise Exception(f"LLM API 호출 실패: {str(e)}")

            # 응답 파싱 및 유효성 검증
            parsed_response = self._parse_response(response.choices[0].message.content)
            validated_response = self._validate_response(parsed_response, context)

            # 메모리 업데이트
            self._update_memory(context, validated_response)

            return validated_response

        except Exception as e:
            return {
                "type": "error",
                "content": str(e),
                "fallback_action": self._get_fallback_action(context)
            }

    def _parse_response(self, response: str) -> Action:
        """LLM 응답을 파싱하여 구조화된 형식으로 변환"""
        try:
            # 응답을 줄 단위로 분리
            lines = response.strip().split('\n')
            parsed_response = {
                "action": None,
                "target": None,
                "reason": None,
                "dialogue": None
            }

            current_field = None
            field_content = []

            # 각 줄을 순회하며 파싱
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 필드 식별
                if line.startswith('행동:'):
                    if field_content and current_field:
                        parsed_response[current_field] = '\n'.join(field_content).strip()
                    current_field = 'action'
                    field_content = [line.replace('행동:', '').strip()]

                elif line.startswith('대상:'):
                    if field_content and current_field:
                        parsed_response[current_field] = '\n'.join(field_content).strip()
                    current_field = 'target'
                    field_content = [line.replace('대상:', '').strip()]

                elif line.startswith('이유:'):
                    if field_content and current_field:
                        parsed_response[current_field] = '\n'.join(field_content).strip()
                    current_field = 'reason'
                    field_content = [line.replace('이유:', '').strip()]

                elif line.startswith('대화:'):
                    if field_content and current_field:
                        parsed_response[current_field] = '\n'.join(field_content).strip()
                    current_field = 'dialogue'
                    field_content = [line.replace('대화:', '').strip()]

                else:
                    if current_field:
                        field_content.append(line)

            # 마지막 필드 처리
            if field_content and current_field:
                parsed_response[current_field] = '\n'.join(field_content).strip()

            # 필수 필드 검증
            if not parsed_response['action']:
                raise ValueError("행동이 지정되지 않았습니다")

            # 행동 타입 정규화
            action_types = {
                "투표": Action.VOTE,
                "지목": Action.ACTION,
                "조사": Action.ACTION,
                "치료": Action.ACTION,
                "대화": Action.DISCUSS,
            }
            parsed_response['action'] = action_types.get(
                parsed_response['action'],
                parsed_response['action']
            )

            return {
                "type": "game_action",
                "content": parsed_response
            }

        except Exception as e:
            # 파싱 실패 시 원본 응답을 그대로 반환
            return {
                "type": "raw_response",
                "content": response,
                "error": str(e)
            }

    def _update_memory(self, context: ContextType, action: Action):
        """메모리 업데이트"""
        memory = {
            "phase": context.get("phase"),
            "day": context.get("day_count"),
            "action": action,
            "context": context
        }
        self.memory_manager.add_memory(memory)

    def update_knowledge(self, new_information: Dict):
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

    def _validate_response(self, response: Dict, context: ContextType) -> Dict:
        """응답의 유효성 검증"""
        if response["type"] == "raw_response":
            return response

        content = response["content"]
        alive_players = context.get("alive_players", [])
        phase = context.get("phase", "")

        # 행동 유효성 검증
        valid_actions = {
            "밤": {
                "마피아": ["지목"],
                "의사": ["치료"],
                "경찰": ["조사"],
                "시민": ["대화"]
            },
            "낮": ["투표", "대화"]
        }

        # 페이즈별 가능한 행동인지 확인
        if phase == "밤":
            allowed_actions = valid_actions["밤"].get(self.role, [])
        else:
            allowed_actions = valid_actions["낮"]

        if content["action"] not in allowed_actions:
            raise ValueError(f"현재 페이즈에서 불가능한 행동입니다: {content['action']}")

        # 대상 플레이어 유효성 검증
        if content["action"] != "대화" and content["target"]:
            if content["target"] not in alive_players:
                raise ValueError(f"존재하지 않는 플레이어입니다: {content['target']}")
            if content["target"] == self.player_id and self.role != "의사":
                raise ValueError("자신을 대상으로 지정할 수 없습니다")

        return response

    def _get_fallback_action(self, context: ContextType) -> Dict:
        """오류 발생 시 기본 행동 반환"""
        phase = context.get("phase", "")
        alive_players = context.get("alive_players", [])

        # 자신을 제외한 생존자 중 무작위 선택
        possible_targets = [p for p in alive_players if p != self.player_id]
        target = random.choice(possible_targets) if possible_targets else None

        if phase == "밤":
            action_map = {
                "마피아": "지목",
                "의사": "치료",
                "경찰": "조사",
                "시민": "대화"
            }
            action = action_map.get(self.role, "대화")
        else:
            action = "투표"

        return {
            "type": "game_action",
            "content": {
                "action": action,
                "target": target,
                "reason": "시스템 오류로 인한 기본 행동",
                "dialogue": "죄송합니다. 기술적인 문제가 발생했습니다."
            }
        }

    def generate_conversation(self, context: ContextType) -> str:
        """대화 생성
        
        Args:
            context: 현재 게임 상태 및 대화 컨텍스트
            
        Returns:
            생성된 대화 내용
        """
        try:
            # AI 응답 생성
            response = self.generate_response(context)
            if response.get("type") == "game_action" and response["content"].get("dialogue"):
                # 대화 내용을 메모리에 저장 (직접 경험)
                self.memory_manager.add_memory({
                    "type": MemoryType.CONVERSATION,
                    "content": response["content"]["dialogue"],
                    "turn": context.get("turn"),
                    "phase": context.get("phase"),
                    "players": [self.player_id],
                    "source": "direct_experience"
                })
                return response["content"]["dialogue"]
            return ""
        except Exception as e:
            return "죄송합니다. 대화 생성 중 오류가 발생했습니다."
