from .base_player import BasePlayer
from ..game.game_state import GameState
from typing import Dict

class Citizen(BasePlayer):
    def __init__(self, name: str):
        super().__init__(name)
        self.role = "시민"
        
    async def take_action(self, game_state: GameState) -> Dict:
        """시민의 전체 의사결정 프로세스"""
        # 시민은 특별한 행동이 없으므로, 대화만 수행
        context = self.memory.get_relevant_memories(game_state)
        message = await self.ai_agent.generate_response(context)
        
        result = {
            "success": True,
            "message": message
        }
        
        self.memory.add_memory({
            "action": "discuss",
            "message": message,
            "turn": game_state.day_count
        })
        
        return result