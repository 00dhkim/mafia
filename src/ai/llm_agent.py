from typing import List, Dict
import openai

class LLMAgent:
    def __init__(self):
        self.conversation_history = []
        self.game_knowledge = {}
        
    async def generate_response(self, context: Dict) -> str:
        """LLM을 사용하여 응답 생성"""
        try:
            # 컨텍스트 구성
            prompt = self._build_prompt(context)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 마피아 게임의 플레이어입니다."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return str(e)
            
    def _build_prompt(self, context: Dict) -> str:
        """컨텍스트를 기반으로 프롬프트 생성"""
        role = context.get("role", "")
        phase = context.get("phase", "")
        alive_players = context.get("alive_players", [])
        memories = context.get("memories", [])
        
        prompt = f"""
        당신의 역할: {role}
        현재 페이즈: {phase}
        생존자 목록: {', '.join(alive_players)}
        
        기억:
        {memories}
        
        다음 행동을 선택하세요.
        """
        
        return prompt
    
    def update_knowledge(self, new_information: Dict):
        """게임 정보 업데이트"""
        pass 