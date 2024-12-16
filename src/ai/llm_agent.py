from typing import List, Dict, Optional
import openai
from .memory_manager import MemoryManager
import random
from .utils.config import GameConfig

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
    def __init__(self, player_id: str, memory_manager: MemoryManager, role: str):
        self.player_id = player_id
        self.role = role
        self.memory_manager = memory_manager
        self.is_alive = True
        self.conversation_history = []
        self.game_knowledge = {
            "known_roles": {},  # 확인된 다른 플레이어의 역할
            "suspicious_players": [],  # 의심스러운 플레이어 목록
            "trusted_players": []  # 신뢰할 수 있는 플레이어 목록
        }
        # 전역 설정에서 AI 설정 가져오기
        self.ai_config = GameConfig().config["ai_settings"]

    def generate_response(self, context: Dict) -> Dict:
        """LLM을 사용하여 응답 생성"""
        try:
            # 컨텍스트 구성
            prompt = self._build_prompt(context)
            relevant_memories = self.memory_manager.get_relevant_memories(context.get("phase", ""))
            
            # 시스템 메시지에 게임 규칙과 제약사항 추가
            system_prompt = self._get_role_prompt() + """

응답 규칙:
1. 반드시 지정된 형식으로만 응답하세요
2. 행동은 [투표/지목/조사/치료/대화] 중에서만 선택하세요
3. 대상은 반드시 생존자 목록에 있는 플레이어만 지정하세요
4. 자신을 대상으로 지정할 수 없습니다 (의사 제외)
5. 이유는 구체적으로 설명해주세요
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            # 이전 대화 기록 추가 (컨텍스트 유지)
            if self.conversation_history:
                messages.extend(self.conversation_history[-3:])  # 최근 3개 대화만 포함

            # 관련 기억 추가
            if relevant_memories:
                memories_prompt = "이전 기억:\n" + "\n".join(relevant_memories)
                messages.append({"role": "assistant", "content": memories_prompt})

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
            
            # 대화 기록 업데이트
            self.conversation_history.append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })
            
            # 메모리 업데이트
            self._update_memory(context, validated_response)
            
            return validated_response
            
        except Exception as e:
            return {
                "type": "error",
                "content": str(e),
                "fallback_action": self._get_fallback_action(context)
            }

    def _get_role_prompt(self) -> str:
        """역할별 기본 프롬프트 반환"""
        base_prompt = """당신은 마피아 게임의 플레이어입니다.

게임 규칙:
1. 게임은 낮과 밤을 반복하며 진행됩니다
2. 게임 구성: 마피아(1명), 의사(1명), 경찰(1명), 시민(1명)
3. 낮에는 모든 생존자가 토론을 하고 투표로 한 명을 처형합니다
4. 밤에는 각자의 역할에 맞는 특수 능력을 사용합니다

승리 조건:
- 시민 팀: 마피아를 찾아내어 제거하면 승리
- 마피아: 시민의 수가 1명이 되면 승리 (의사/경찰도 시민으로 계산)

행동 지침:
1. 자신의 역할을 직접적으로 밝히지 마세요
2. 다른 플레이어들의 행동을 관찰하고 분석하세요
3. 논리적인 추론을 통해 의사결정을 하세요
4. 게임의 흐름을 고려하여 전략적으로 행동하세요
"""
        
        role_prompts = {
            "마피아": """당신은 마피아입니다.
- 임무: 다른 플레이어들에게 정체를 숨기고 시민을 제거
- 특수 능력: 밤에 한 명을 지목하여 제거 가능
- 전략:
  * 시민인 척 자연스럽게 행동하세요
  * 다른 시민들의 신뢰를 얻으세요
  * 의사와 경찰을 우선적으로 제거하는 것이 유리합니다
  * 자신에 대한 의심을 다른 사람에게 돌리세요""",

            "의사": """당신은 의사입니다.
- 임무: 마피아의 공격으로부터 시민을 보호
- 특수 능력: 밤마다 한 명을 선택하여 보호
- 전략:
  * 자신의 정체를 직접적으로 밝히지 마세요
  * 마피아의 다음 타겟을 예측하여 보호하세요
  * 보호 기록을 잘 기억하고 활용하세요
  * 경찰을 찾아 협력할 방법을 모색하세요""",

            "경찰": """당신은 경찰입니다.
- 임무: 마피아의 정체를 밝혀내어 시민들을 보호
- 특수 능력: 밤마다 한 명의 직업 확인 가능
- 전략:
  * 조사 결과를 직접적으로 공개하지 마세요
  * 의심스러운 행동을 보이는 플레이어를 우선 조사하세요
  * 조사 결과를 바탕으로 은밀히 시민들을 설득하세요
  * 의사과 협력할 방법을 모색하세요""",

            "시민": """당신은 시민입니다.
- 임무: 마피아를 찾아내어 처형하는데 협력
- 특수 능력: 없음
- 전략:
  * 모든 대화와 투표를 주의 깊게 관찰하세요
  * 의심스러운 행동을 하는 플레이어를 메모하세요
  * 다른 플레이어들의 주장을 분석하세요
  * 투표 전 충분한 논의를 통해 신중하게 결정하세요"""
        }
        
        return base_prompt + role_prompts.get(self.role, "")

    def _build_prompt(self, context: Dict) -> str:
        """컨텍스트를 기반으로 프롬프트 생성"""
        phase = context.get("phase", "")
        alive_players = context.get("alive_players", [])
        day_count = context.get("day_count", 0)
        last_killed = context.get("last_killed", "없음")
        vote_history = context.get("vote_history", [])
        
        prompt = f"""
현재 게임 상황:
- {day_count}일차 {phase}
- 생존자 ({len(alive_players)}명): {', '.join(alive_players)}
- 마지막 사망자: {last_killed}

당신의 정보:
- 확인된 역할: {', '.join([f"{p}({r})" for p, r in self.game_knowledge['known_roles'].items()])}
- 의심스러운 플레이어: {', '.join(self.game_knowledge['suspicious_players'])}
- 신뢰할 수 있는 플레이어: {', '.join(self.game_knowledge['trusted_players'])}

{self._get_phase_specific_prompt(phase, context)}

응답 형식:
행동: [투표/지목/조사/치료/대화] 중 선택
대상: [플레이어 이름]
이유: [상세한 의사결정 이유]
대화: [다른 플레이어들과 나눌 대화 내용]
"""
        return prompt

    def _get_phase_specific_prompt(self, phase: str, context: Dict) -> str:
        """페이즈별 특수 프롬프트 반환"""
        if phase == "밤":
            if self.role == "마피아":
                return """당신의 차례입니다.
- 제거할 대상을 선택하세요
- 의사와 경찰을 우선적으로 노리는 것이 유리합니다
- 패턴이 예측되지 않도록 주의하세요
- 낮에 의심받지 않도록 전략적으로 선택하세요"""

            elif self.role == "의사":
                return """당신의 차례입니다.
- 보호할 대상을 선택하세요
- 마피아의 다음 타겟을 예측해보세요
- 중요한 역할을 가진 것으로 의심되는 플레이어를 보호하세요
- 자신을 보호할 수도 있습니다"""

            elif self.role == "경찰":
                return """당신의 차례입니다.
- 조사할 대상을 선택하세요
- 의심스러운 행동을 보인 플레이어를 우선 조사하세요
- 조사 결과를 잘 기억했다가 낮에 활용하세요
- 마피아를 찾아내면 낮에 은밀히 다른 플레이어들을 설득하세요"""

        elif phase == "낮":
            recent_deaths = context.get("recent_deaths", [])
            death_info = f"최근 사망자: {', '.join(recent_deaths)}" if recent_deaths else "사망자 없음"
            
            return f"""토론 및 투표 시간입니다.
{death_info}

다음을 고려하여 행동하세요:
1. 어제 밤의 사건에 대해 분석하세요
2. 의심스러운 행동을 한 플레이어를 지적하세요
3. 자신의 의견을 논리적으로 설명하세요
4. 다른 플레이어들의 주장을 잘 경청하세요
5. 현재 생존자 수를 고려하여 신중하게 투표하세요"""

        return ""

    def _parse_response(self, response: str) -> Dict:
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
                '투표': 'vote',
                '지목': 'target',
                '조사': 'investigate',
                '치료': 'heal',
                '대화': 'chat'
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

    def _update_memory(self, context: Dict, action: Dict):
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

    def _validate_response(self, response: Dict, context: Dict) -> Dict:
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

    def _get_fallback_action(self, context: Dict) -> Dict:
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

    def generate_conversation(self, context: Dict) -> str:
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