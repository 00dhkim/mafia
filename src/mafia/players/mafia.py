from typing import Dict

from mafia.players.base_player import BasePlayer
from mafia.utils.enum import ActionType, ContextType


class Mafia(BasePlayer):

    def take_action(self, context: ContextType) -> ActionType:
        """마피아의 밤 행동 수행"""
        if game_state.current_phase != GamePhase.NIGHT:
            return {"success": False, "message": "밤이 아닙니다"}

        context = {
            "role": self.role,
            "phase": "밤",
            "alive_players": [p.name for p in game_state.alive_players if p != self],
            "memories": self.memory_manager.get_recent_memories(game_state.day_count)
        }

        target_name = self.ai_agent.generate_response(context)
        target = self._validate_and_get_target(
            target_name=target_name,
            candidates=game_state.alive_players,
            name_selector=lambda p: p.name,
            exclude_self=True
        )

        if not target:
            return {"success": False, "message": "대상을 찾을 수 없습니다"}

        result = self._kill(target)

        self.memory.add_memory({
            "action": "kill",
            "target": target.name,
            "result": result,
            "turn": game_state.day_count
        })

        return result

    def _kill(self, target_player) -> Dict:
        """실제 살해 행동 수행"""
        if not target_player.is_alive:
            return {"success": False, "message": "이미 사망한 플레이어입니다"}

        if target_player.is_healed:
            return {"success": False, "message": "의사에 의해 보호되었습니다"}

        target_player.is_alive = False
        return {
            "success": True,
            "message": f"{target_player.name}을(를) 살해했습니다"
        }
