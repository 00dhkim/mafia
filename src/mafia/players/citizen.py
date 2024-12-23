from typing import Dict

from mafia.players.base_player import BasePlayer
from mafia.utils.enum import ActionType, ContextType


class Citizen(BasePlayer):

    def take_action(self, context: ContextType) -> ActionType:
        """시민의 전체 의사결정 프로세스"""
        # 시민은 특별한 행동이 없으므로, 대화만 수행
        context = self.memory_manager.get_recent_memories(game_state.day)
        message = self.ai_agent.generate_response(context)

        result = {
            "success": True,
            "message": message
        }

        self.memory.add_memory({"action": "discuss", "message": message, "turn": game_state.day})

        return result
