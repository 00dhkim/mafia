from typing import Dict
import openai
from models.role import Role, ROLE_DESCRIPTIONS

class Player:
    def __init__(self, name: str, role: Role):
        self.name = name
        self.role = role
        self.is_alive = True
        self.knowledge = {}
        self.game = None
        
    async def generate_response(self, prompt: str) -> str:
        print(f"\n{self.name} ({self.role.value}) 응답 생성 중...")
        try:
            async with openai.AsyncOpenAI() as client:
                response = await client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": self._get_base_prompt()},
                        {"role": "user", "content": prompt}
                    ],
                    timeout=30
                )
                result = response.choices[0].message.content
                print(f"{self.name}의 응답: {result}")
                return result
        except Exception as e:
            print(f"오류 발생 ({self.name}): {e}")
            return "응답을 생성할 수 없습니다."

    def _get_base_prompt(self) -> str:
        return f"""당신은 마피아 게임의 {self.name}입니다.
역할: {self.role.value}
능력: {ROLE_DESCRIPTIONS[self.role]}
승리 조건: {'마피아를 모두 제거' if self.role != Role.MAFIA else '시민의 수가 마피아 이하가 되도록'}
""" 