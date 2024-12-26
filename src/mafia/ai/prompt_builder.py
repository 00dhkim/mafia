"""
LLM 모델에게 입력할 프롬프트를 문자열로 반환하는 함수들
"""
from typing import Any
from mafia.utils.enum import ContextType, GamePhase, Role


def _rule_prompt():
    return """당신은 마피아 게임의 플레이어입니다.

게임 기본 규칙:
- 모든 플레이어는 대화와 특수 능력을 통해 팀의 목표를 이뤄야 합니다.
- 게임은 마피아(1명), 의사(1명), 경찰(1명), 시민(1명)으로 구성되며, 마피아는 마피아팀, 그 외의 직업은 시민팀에 속합니다.
- 마피아팀은 시민의 수가 1명이 되면 승리하며, 시민팀은 마피아를 찾아내어 제거하면 승리합니다.
- 게임은 '낮 대화', '낮 추리', '낮 투표', '밤 행동' 페이즈를 반복하여 진행됩니다.
- '낮 대화' 페이즈에는 각 플레이어가 자신의 역할을 숨기고 다른 플레이어들과 대화를 나눕니다.
- '낮 추리' 페이즈에는 그동안의 기억을 정리하고 각자의 직업을 추리합니다.
- '낮 투표' 페이즈에는 마피아로 의심가는 사람을 지목하여 투표를 통해 처형할 수 있습니다. 이때 최다득표자가 2명 이상일 경우, 투표는 무산됩니다.
- '밤 행동' 페이즈에는 마피아는 시민 중 한 명을 공격하고, 의사는 한 명을 지목하여 마피아의 공격으로부터 보호하며, 경찰은 한 명을 지목하여 마피아 여부를 확인합니다. '밤 행동' 페이즈동안의 모든 행동은 본인만이 알 수 있습니다.

행동 양식:
- 자신의 역할을 기본적으로 숨기는 것이 좋습니다.
- 다른 플레이어들의 발언을 관찰하고 분석하세요.
- 논리적인 추론을 통해 의사결정을 하세요.
- 게임의 흐름을 고려하여 전략적으로 행동하세요."""


def _role_prompt(name: str, role: Role):

    if role == Role.MAFIA:
        return f"""당신의 정보:
- 이름: {name}
- 직업: 마피아
- 임무: 다른 플레이어들에게 정체를 숨기고 시민을 제거
- 특수 능력: 밤에 한 명을 지목하여 제거 가능
- 전략:
  * 시민편인 척 자연스럽게 행동하세요
  * 의사와 경찰을 우선적으로 제거하는 것이 유리합니다
  * 자신에 대한 의심을 다른 사람에게 돌리세요
  * 지금까지의 기억을 잘 활용하세요
  * 게임의 최종 목표를 염두하여 승리하기 위한 최선의 결정을 내리세요"""

    elif role == Role.DOCTOR:
        return f"""당신의 정보:
- 이름: {name}
- 직업: 의사
- 임무: 마피아의 공격으로부터 시민을 보호
- 특수 능력: 밤마다 한 명(본인 포함)을 선택하여 마피아의 공격으로부터 보호
- 전략:
  * 자신의 정체를 직접적으로 밝히지 마세요
  * 마피아의 다음 타겟을 예측하여 보호하세요
  * 지금까지의 기억을 잘 활용하세요
  * 게임의 최종 목표를 염두하여 마피아의 공격으로부터 보호하기 위한 최선의 결정을 내리세요"""

    elif role == Role.POLICE:
        return f"""당신의 정보:
- 이름: {name}
- 직업: 경찰
- 임무: 마피아의 정체를 밝혀내어 시민들을 보호
- 특수 능력: 밤마다 한 명을 지목하여 마피아인지 아닌지 조사
- 전략:
  * 의심스러운 행동을 보이는 플레이어를 우선 조사하세요
  * 조사 결과를 바탕으로 은밀히 시민들을 설득하세요
  * 지금까지의 기억을 잘 활용하세요
  * 게임의 최종 목표를 염두하여 마피아를 찾아내기 위한 최선의 결정을 내리세요"""

    elif role == Role.CITIZEN:
        return f"""당신의 정보:
- 이름: {name}
- 직업: 시민
- 임무: 마피아를 찾아내어 투표로 처형
- 특수 능력: 없음
- 전략:
  * 모든 대화와 투표를 주의 깊게 관찰하세요
  * 다른 플레이어들의 주장을 분석하세요
  * 투표 전 충분한 논의를 통해 신중하게 결정하세요
  * 지금까지의 기억을 잘 활용하세요
  * 게임의 최종 목표를 염두하여 승리하기 위한 최선의 결정을 내리세요"""


def _context_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    return f"""현재 게임 상황:
- {context.get("day_count", 0)}일차 {context.get("phase", "")} 페이즈
- 생존자: {len(context.get("alive_players", []))}명 ({', '.join(context.get("alive_players", []))})

알고있는 정보:
- 확인된 역할: {', '.join([f"{p}({r})" for p, r in game_knowledge.get('known_roles', {}).items()])}
- 의심스러운 플레이어: {', '.join(game_knowledge.get('suspicious_players', []))}
- 신뢰할 수 있는 플레이어: {', '.join(game_knowledge.get('trusted_players', []))}"""


def system_prompt(name: str, role: Role):
    return _rule_prompt() + "\n\n" + _role_prompt(name, role)


###################################
# 1번 페이즈
def day_conversation_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.DAY_CONVERSATION, "낮 대화 페이즈가 아닙니다"

    conversation_prompt = """현재는 '낮 대화' 페이즈입니다.

응답 규칙:
1. 자유롭게 발언하세요
2. 어제 밤의 사건에 대해 분석하세요
3. 의심스러운 행동을 한 플레이어를 지적하세요
4. 자신의 의견을 논리적으로 설명하세요"""

    return _context_prompt(context, game_knowledge) + "\n\n" + conversation_prompt

###################################
# 2번 페이즈
def day_reasoning_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.DAY_REASONING, "낮 추리 페이즈가 아닙니다"

    reasoning_prompt = """현재는 '낮 추리' 페이즈입니다.

응답 규칙:
# TODO: known_roles, suspicious_players, trusted_players
"""

    # raise NotImplementedError
    return _context_prompt(context, game_knowledge) + "\n" + reasoning_prompt

###################################
# 3번 페이즈
def day_vote_prompt(context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.DAY_VOTE, "낮 투표 페이즈가 아닙니다"

    vote_prompt = """현재는 '낮 투표' 페이즈입니다.

고려사항:
1. 반드시 지정된 형식으로만 응답하세요
2. 대상은 반드시 생존자 목록에 있는 플레이어만 지정하세요. 단, 투표를 건너뛰기를 희망하는 경우 "없음"으로 응답하세요
3. 이유는 구체적으로 설명해주세요
4. 현재 생존자 수를 고려하여 신중하게 투표하세요

응답 규칙:
대상: [플레이어 이름]
이유: [상세한 투표 이유]"""

    return _context_prompt(context, game_knowledge) + "\n\n" + vote_prompt

###################################
# 4번 페이즈
def night_action_prompt(role: Role, context: ContextType, game_knowledge: dict[str, Any]):
    assert context.get("phase") == GamePhase.NIGHT_ACTION, "밤 행동 페이즈가 아닙니다"

    if role == Role.MAFIA:
        role_specific = """- 제거할 대상을 선택하세요
- 의사와 경찰을 우선적으로 노리는 것이 유리합니다
- 패턴이 예측되지 않도록 주의하세요"""

    elif role == Role.DOCTOR:
        role_specific = """- 보호할 대상을 선택하세요
- 마피아의 다음 타겟을 예측해보세요
- 중요한 역할을 가진 것으로 예상되는 플레이어를 보호하세요
- 자신을 보호할 수도 있습니다"""

    elif role == Role.POLICE:
        role_specific = """- 조사할 대상을 선택하세요
- 의심스러운 행동을 보인 플레이어를 우선 조사하세요
- 조사 결과를 잘 기억했다가 낮에 활용하세요
- 마피아를 찾아내면 낮에 다른 플레이어들을 설득하세요"""

    else:
        raise ValueError(f"올바르지 않은 역할입니다: {role}")

    action_prompt = f"""현재는 '밤 행동' 페이즈입니다.

고려사항:
- 반드시 지정된 형식으로만 응답하세요
{role_specific}

응답 규칙:
대상: [플레이어 이름]
이유: [대상을 선택한 구체적인 이유]"""

    return _context_prompt(context, game_knowledge) + "\n\n" + action_prompt


def generate_prompt_examples():
    name = "Alice"
    role = Role.POLICE
    game_knowledge = {
        "known_roles": {"Bob": Role.MAFIA, "Charlie": Role.CITIZEN},
        "suspicious_players": ["David"],
        "trusted_players": ["Eve"],
    }

    examples = {
        "system prompt": system_prompt(name, role),
        GamePhase.DAY_CONVERSATION: day_conversation_prompt(
            {
                "phase": GamePhase.DAY_CONVERSATION,
                "day_count": 1,
                "alive_players": ["Alice", "Bob", "Charlie", "David"],
            },
            game_knowledge,
        ),
        GamePhase.DAY_REASONING: day_reasoning_prompt(
            {
                "phase": GamePhase.DAY_REASONING,
                "day_count": 1,
                "alive_players": ["Alice", "Bob", "Charlie", "David"],
            },
            game_knowledge,
        ),
        GamePhase.DAY_VOTE: day_vote_prompt(
            {
                "phase": GamePhase.DAY_VOTE,
                "day_count": 1,
                "alive_players": ["Alice", "Bob", "Charlie", "David"],
            },
            game_knowledge,
        ),
        GamePhase.NIGHT_ACTION: night_action_prompt(
            Role.POLICE,
            {
                "phase": GamePhase.NIGHT_ACTION,
                "day_count": 1,
                "alive_players": ["Alice", "Bob", "Charlie", "David"],
            },
            game_knowledge,
        ),
    }

    with open("/workspaces/mafia/docs/prompt_examples.md", "w", encoding="utf-8") as f:
        f.write("# 각 페이즈 별 프롬프트 예시\n\n")
        f.write("*This file is generated by prompt_builder.py*\n\n")

        for phase, prompt in examples.items():
            f.write(f"## {phase}\n\n")
            f.write("- 입력\n")
            f.write("```\n")
            f.write(prompt)
            f.write("\n```\n\n")

            if phase == GamePhase.DAY_CONVERSATION:
                f.write("- 출력\n")
                f.write("```\n")
                f.write(
                    "저는 아직 누구를 믿어야 할지 모르겠어요. 더 많은 정보를 얻어야 할 것 같아요.\n"
                )
                f.write("```\n\n")
            if phase == GamePhase.DAY_REASONING:
                f.write("- 출력\n")
                f.write("```\n")
                f.write("TODO:\n")
                f.write("```\n\n")
            elif phase == GamePhase.DAY_VOTE:
                f.write("- 출력\n")
                f.write("```\n")
                f.write("대상: Alice\n")
                f.write(
                    "이유: Alice가 낮 대화에서 다른 사람들을 의심하는 발언을 많이 했기 때문에 그녀가 마피아일 가능성이 높다고 생각합니다.\n"
                )
                f.write("```\n\n")
            elif phase == GamePhase.NIGHT_ACTION:
                f.write("- 출력\n")
                f.write("```\n")
                f.write("대상: Bob\n")
                f.write(
                    "이유: Bob이 낮 대화에서 말이 많지 않았고, 다른 사람들의 발언을 잘 듣고 있었기 때문에 Bob을 조사하기로 결정했습니다.\n"
                )
                f.write("```\n\n")


if __name__ == "__main__":
    generate_prompt_examples()
