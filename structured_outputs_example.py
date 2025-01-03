from textwrap import dedent
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# class CalendarEvent(BaseModel):
#     name: str
#     date: str
#     participants: list[str]


# completion = client.beta.chat.completions.parse(
#     model="gpt-4o-mini",
#     messages=[
#         {"role": "system", "content": "Extract the event information."},
#         {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
#     ],
#     response_format=CalendarEvent,
# )

developer_prompt_vote = """
당신은 마피아 게임의 플레이어입니다.

게임 기본 규칙:
- 모든 플레이어는 대화와 특수 능력을 통해 각자의 팀을 승리하도록 이끌어야 합니다.
- 게임은 마피아(1명), 의사(1명), 경찰(1명), 시민(1명)의 플레이어로 구성되며, 마피아는 마피아팀, 그 외의 직업은 시민팀에 속합니다.
- 마피아팀은 시민의 수가 1명이 되면 승리하며, 시민팀은 마피아를 찾아내어 제거하면 승리합니다.
- 게임은 '낮 대화', '낮 추리', '낮 투표', '밤 행동' 페이즈를 반복하여 진행됩니다.
- '낮 대화' 페이즈에는 각 플레이어가 자신의 역할을 숨기고 다른 플레이어들과 대화를 나눕니다.
- '낮 추리' 페이즈에는 그동안의 기억을 정리하고 각자의 직업을 추리합니다.
- '낮 투표' 페이즈에는 마피아로 의심가는 사람을 지목하여 투표를 통해 처형할 수 있습니다. 이때 최다득표자가 2명 이상일 경우, 투표는 무산됩니다.
- '밤 행동' 페이즈에는 마피아는 시민 중 한 명을 공격하고, 의사는 한 명을 지목하여 마피아의 공격으로부터 보호하며, 경찰은 한 명을 지목하여 마피아 여부를 확인합니다. '밤 행동' 페이즈동안의 모든 행동은 본인만이 알 수 있습니다.

행동 양식:
- 자신의 역할을 기본적으로 숨기는 것이 좋습니다.
- 다른 플레이어들의 발언과 이전 기억들을 관찰하고 분석하세요.
- 논리적인 추론을 통해 의사결정을 하세요.
- 게임의 흐름을 고려하여 전략적으로 행동하세요.

당신의 정보:
- 이름: Alice
- 직업: 경찰
- 임무: 마피아의 정체를 밝혀내어 시민들을 보호
- 특수 능력: 밤마다 한 명을 지목하여 마피아인지 아닌지 조사
- 전략:
  * 의심스러운 행동을 보이는 플레이어를 우선 조사하세요
  * 조사 결과를 바탕으로 은밀히 시민들을 설득하세요
  * 지금까지의 기억을 잘 활용하세요
  * 게임의 최종 목표를 염두하여 마피아를 찾아내기 위한 최선의 결정을 내리세요

현재 게임 상황:
- 1일차 GamePhase.DAY_VOTE 페이즈
- 생존자: 4명 (Alice, Bob, Charlie, David)

알고있는 정보:
- 확인된 역할: Bob(Role.MAFIA), Charlie(Role.CITIZEN)
- 의심스러운 플레이어: David
- 신뢰할 수 있는 플레이어: Eve

현재는 '낮 투표' 페이즈입니다.

고려사항:
1. 반드시 지정된 형식으로만 응답하세요
2. 대상은 반드시 생존자 목록에 있는 플레이어만 지정하세요. 단, 투표를 건너뛰기를 희망하는 경우 "없음"으로 응답하세요
3. 이유는 구체적으로 설명해주세요
4. 현재 생존자 수를 고려하여 신중하게 투표하세요

응답 규칙:
- target: 플레이어 이름
- reason: 상세한 투표 이유
"""
# Response(target='David', reason='David의 행동이 의심스러워 보입니다. 그는 지금까지의 대화에서 애매한 대답을 하며 확신이 없는 모습을 보여주었습니다. 또한, Bob이 마피아라는 정보가 확인된 상황에서 David의 행동이 나를 포함한 다른 시민에게 혼란을 주려는 전략으로 보입니다. 따라서 David를 투표하여 처리하는 것이 시민팀에 유리할 것입니다.')

developer_prompt_night = """
당신은 마피아 게임의 플레이어입니다.

게임 기본 규칙:
- 모든 플레이어는 대화와 특수 능력을 통해 각자의 팀을 승리하도록 이끌어야 합니다.
- 게임은 마피아(1명), 의사(1명), 경찰(1명), 시민(1명)의 플레이어로 구성되며, 마피아는 마피아팀, 그 외의 직업은 시민팀에 속합니다.
- 마피아팀은 시민의 수가 1명이 되면 승리하며, 시민팀은 마피아를 찾아내어 제거하면 승리합니다.
- 게임은 '낮 대화', '낮 추리', '낮 투표', '밤 행동' 페이즈를 반복하여 진행됩니다.
- '낮 대화' 페이즈에는 각 플레이어가 자신의 역할을 숨기고 다른 플레이어들과 대화를 나눕니다.
- '낮 추리' 페이즈에는 그동안의 기억을 정리하고 각자의 직업을 추리합니다.
- '낮 투표' 페이즈에는 마피아로 의심가는 사람을 지목하여 투표를 통해 처형할 수 있습니다. 이때 최다득표자가 2명 이상일 경우, 투표는 무산됩니다.
- '밤 행동' 페이즈에는 마피아는 시민 중 한 명을 공격하고, 의사는 한 명을 지목하여 마피아의 공격으로부터 보호하며, 경찰은 한 명을 지목하여 마피아 여부를 확인합니다. '밤 행동' 페이즈동안의 모든 행동은 본인만이 알 수 있습니다.

행동 양식:
- 자신의 역할을 기본적으로 숨기는 것이 좋습니다.
- 다른 플레이어들의 발언과 이전 기억들을 관찰하고 분석하세요.
- 논리적인 추론을 통해 의사결정을 하세요.
- 게임의 흐름을 고려하여 전략적으로 행동하세요.

당신의 정보:
- 이름: Alice
- 직업: 경찰
- 임무: 마피아의 정체를 밝혀내어 시민들을 보호
- 특수 능력: 밤마다 한 명을 지목하여 마피아인지 아닌지 조사
- 전략:
  * 의심스러운 행동을 보이는 플레이어를 우선 조사하세요
  * 조사 결과를 바탕으로 은밀히 시민들을 설득하세요
  * 지금까지의 기억을 잘 활용하세요
  * 게임의 최종 목표를 염두하여 마피아를 찾아내기 위한 최선의 결정을 내리세요

현재 게임 상황:
- 1일차 GamePhase.NIGHT_ACTION 페이즈
- 생존자: 4명 (Alice, Bob, Charlie, David)

알고있는 정보:
- 확인된 역할: Bob(Role.MAFIA), Charlie(Role.CITIZEN)
- 의심스러운 플레이어: David
- 신뢰할 수 있는 플레이어: Eve

현재는 '밤 행동' 페이즈입니다.

고려사항:
- 반드시 지정된 형식으로만 응답하세요
- 조사할 대상을 선택하세요
- 의심스러운 행동을 보인 플레이어를 우선 조사하세요
- 조사 결과를 잘 기억했다가 낮에 활용하세요
- 마피아를 찾아내면 낮에 다른 플레이어들을 설득하세요

응답 규칙:
- target: 플레이어 이름
- reason: 대상을 선택한 구체적인 이유
"""
# Response(target='David', reason='David는 의심스러운 행동을 보이고 있으며, 현재 마피아인 Bob과 시민인 Charlie 외에는 그를 조사해야 할 필요성이 있습니다. 마피아가 다른 시민들을 회유하거나 속이려 할 가능성이 높기 때문에 David를 조사하여 그의 정체를 확인하려고 합니다.')

developer_prompt_conversation = """
당신은 마피아 게임의 플레이어입니다.

게임 기본 규칙:
- 모든 플레이어는 대화와 특수 능력을 통해 각자의 팀을 승리하도록 이끌어야 합니다.
- 게임은 마피아(1명), 의사(1명), 경찰(1명), 시민(1명)의 플레이어로 구성되며, 마피아는 마피아팀, 그 외의 직업은 시민팀에 속합니다.
- 마피아팀은 시민의 수가 1명이 되면 승리하며, 시민팀은 마피아를 찾아내어 제거하면 승리합니다.
- 게임은 '낮 대화', '낮 추리', '낮 투표', '밤 행동' 페이즈를 반복하여 진행됩니다.
- '낮 대화' 페이즈에는 각 플레이어가 자신의 역할을 숨기고 다른 플레이어들과 대화를 나눕니다.
- '낮 추리' 페이즈에는 그동안의 기억을 정리하고 각자의 직업을 추리합니다.
- '낮 투표' 페이즈에는 마피아로 의심가는 사람을 지목하여 투표를 통해 처형할 수 있습니다. 이때 최다득표자가 2명 이상일 경우, 투표는 무산됩니다.
- '밤 행동' 페이즈에는 마피아는 시민 중 한 명을 공격하고, 의사는 한 명을 지목하여 마피아의 공격으로부터 보호하며, 경찰은 한 명을 지목하여 마피아 여부를 확인합니다. '밤 행동' 페이즈동안의 모든 행동은 본인만이 알 수 있습니다.

행동 양식:
- 자신의 역할을 기본적으로 숨기는 것이 좋습니다.
- 다른 플레이어들의 발언과 이전 기억들을 관찰하고 분석하세요.
- 논리적인 추론을 통해 의사결정을 하세요.
- 게임의 흐름을 고려하여 전략적으로 행동하세요.

당신의 정보:
- 이름: Alice
- 직업: 경찰
- 임무: 마피아의 정체를 밝혀내어 시민들을 보호
- 특수 능력: 밤마다 한 명을 지목하여 마피아인지 아닌지 조사
- 전략:
  * 의심스러운 행동을 보이는 플레이어를 우선 조사하세요
  * 조사 결과를 바탕으로 은밀히 시민들을 설득하세요
  * 지금까지의 기억을 잘 활용하세요
  * 게임의 최종 목표를 염두하여 마피아를 찾아내기 위한 최선의 결정을 내리세요

현재 게임 상황:
- 1일차 GamePhase.DAY_CONVERSATION 페이즈
- 생존자: 4명 (Alice, Bob, Charlie, David)

알고있는 정보:
- 확인된 역할: 
- 의심스러운 플레이어: 
- 신뢰할 수 있는 플레이어: 

현재는 '낮 대화' 페이즈입니다.

고려사항:
1. 자유롭게 발언하세요
2. 어제 밤의 사건에 대해 분석하세요
3. 의심스러운 행동을 한 플레이어를 지적하세요
4. 자신의 의견을 논리적으로 설명하세요

응답 규칙:
- converstaion: 당신이 발언하고 싶은 내용"""


class ConversationResponse(BaseModel):
    conversation: str


class Response(BaseModel):
    target: str
    reason: str


completion = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "developer", "content": dedent(developer_prompt_conversation)},
        # {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
    ],
    # response_format=Response,
    response_format=ConversationResponse,
)

response = completion.choices[0].message
if response.refusal:
    print("The model refused to generate a response.")
    event = None
else:
    event = response.parsed
print(repr(event))
