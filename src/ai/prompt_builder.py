"""
LLM 모델에게 입력할 프롬프트를 문자열로 반환하는 함수들
"""
from typing import Any
from utils.enum import ContextType, GamePhase, Role


def _rule_prompt():
    return """당신은 마피아 게임의 플레이어입니다.

게임 규칙:
1. 게임은 '낮 대화', '낮 추리', '낮 투표', '밤 행동' 페이즈를 반복하여 진행됩니다
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
4. 게임의 흐름을 고려하여 전략적으로 행동하세요"""
# TODO: 행동 지침을 고도화할 필요가 있다.
# 역할 밝혀도 되는 경우 있음. 행동을 관찰하기보단 말을 분석하여 추리함. 논리보단 정치??


def _role_prompt(role: Role):

    if role == Role.MAFIA:
        return """당신은 마피아입니다.
- 임무: 다른 플레이어들에게 정체를 숨기고 시민을 제거
- 특수 능력: 밤에 한 명을 지목하여 제거 가능
- 전략:
  * 시민편인 척 자연스럽게 행동하세요
  * 다른 시민들의 신뢰를 얻으세요
  * 의사와 경찰을 우선적으로 제거하는 것이 유리합니다
  * 자신에 대한 의심을 다른 사람에게 돌리세요"""

    elif role == Role.DOCTOR:
        return """당신은 의사입니다.
- 임무: 마피아의 공격으로부터 시민을 보호
- 특수 능력: 밤마다 한 명을 선택하여 보호
- 전략:
  * 자신의 정체를 직접적으로 밝히지 마세요
  * 마피아의 다음 타겟(본인 포함)을 예측하여 보호하세요
  * 보호 기록을 잘 기억하고 활용하세요
  * 경찰을 찾아 협력할 방법을 모색하세요"""

    elif role == Role.POLICE:
        return """당신은 경찰입니다.
- 임무: 마피아의 정체를 밝혀내어 시민들을 보호
- 특수 능력: 밤마다 한 명의 직업 확인 가능
- 전략:
  * 조사 결과를 직접적으로 공개하지 마세요
  * 의심스러운 행동을 보이는 플레이어를 우선 조사하세요
  * 조사 결과를 바탕으로 은밀히 시민들을 설득하세요
  * 의사과 협력할 방법을 모색하세요"""

    elif role == Role.CITIZEN:
        return """당신은 시민입니다.
- 임무: 마피아를 찾아내어 처형하는데 협력
- 특수 능력: 없음
- 전략:
  * 모든 대화와 투표를 주의 깊게 관찰하세요
  * 의심스러운 행동을 하는 플레이어를 메모하세요
  * 다른 플레이어들의 주장을 분석하세요
  * 투표 전 충분한 논의를 통해 신중하게 결정하세요"""

def _context_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    return f"""현재 게임 상황:
- {context.get("day_count", 0)}일차 {context.get("phase", "")}
- 생존자 ({len(context.get("alive_players", []))})

당신의 정보:
- 확인된 역할: {', '.join([f"{p}({r})" for p, r in game_knowledge.get('known_roles', {}).items()])}
- 의심스러운 플레이어: {', '.join(game_knowledge.get('suspicious_players', []))}
- 신뢰할 수 있는 플레이어: {', '.join(game_knowledge.get('trusted_players', []))}"""

def system_prompt(role: Role):
    return _rule_prompt() + "\n" + _role_prompt(role)

###################################
# 1번 페이즈
def day_conversation_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.DAY_CONVERSATION, "낮 대화 페이즈가 아닙니다"

    conversation_prompt = """낮이 되었습니다. 토론 시간입니다.

응답 규칙:
1. 자유롭게 발언하세요
2. 어제 밤의 사건에 대해 분석하세요
3. 의심스러운 행동을 한 플레이어를 지적하세요
4. 자신의 의견을 논리적으로 설명하세요"""

    return _context_prompt(context, game_knowledge) + "\n" + conversation_prompt

###################################
# 2번 페이즈
def day_reasoning_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.DAY_REASONING, "낮 추리 페이즈가 아닙니다"

    reasoning_prompt = """추리 시간입니다.

응답 규칙:
# TODO: known_roles, suspicious_players, trusted_players
"""

    raise NotImplementedError
    return _context_prompt(context, game_knowledge) + "\n" + reasoning_prompt

###################################
# 3번 페이즈
def day_vote_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.DAY_VOTE, "낮 투표 페이즈가 아닙니다"

    vote_prompt = """투표 시간입니다.

고려사항:
1. 반드시 지정된 형식으로만 응답하세요
2. 대상은 반드시 생존자 목록에 있는 플레이어만 지정하세요. 단, 투표를 건너뛰기를 희망하는 경우 "없음"으로 응답하세요
3. 이유는 구체적으로 설명해주세요
4. 현재 생존자 수를 고려하여 신중하게 투표하세요

응답 규칙:
대상: [플레이어 이름]
이유: [상세한 투표 이유]"""

    return _context_prompt(context, game_knowledge) + "\n" + vote_prompt

###################################
# 4번 페이즈
def night_action_prompt(role: Role, context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.NIGHT_ACTION, "밤 행동 페이즈가 아닙니다"

    if role == Role.MAFIA:
        action_prompt = """밤이 되었습니다. 당신의 차례입니다.

고려사항:
- 제거할 대상을 선택하세요
- 반드시 지정된 형식으로만 응답하세요
- 의사와 경찰을 우선적으로 노리는 것이 유리합니다
- 패턴이 예측되지 않도록 주의하세요

응답 규칙:
대상: [플레이어 이름]
이유: [상세한 선택 이유]"""

    elif role == Role.DOCTOR:
        action_prompt = """밤이 되었습니다. 당신의 차례입니다.

고려사항:
- 보호할 대상을 선택하세요
- 반드시 지정된 형식으로만 응답하세요
- 마피아의 다음 타겟을 예측해보세요
- 중요한 역할을 가진 것으로 의심되는 플레이어를 보호하세요
- 자신을 보호할 수도 있습니다

응답 규칙:
대상: [플레이어 이름]
이유: [상세한 선택 이유]"""

    elif role == Role.POLICE:
        action_prompt = """밤이 되었습니다. 당신의 차례입니다.

고려사항:
- 조사할 대상을 선택하세요
- 반드시 지정된 형식으로만 응답하세요
- 의심스러운 행동을 보인 플레이어를 우선 조사하세요
- 조사 결과를 잘 기억했다가 낮에 활용하세요
- 마피아를 찾아내면 낮에 다른 플레이어들을 설득하세요

응답 규칙:
대상: [플레이어 이름]
이유: [상세한 선택 이유]"""

    return _context_prompt(context, game_knowledge) + "\n" + action_prompt
