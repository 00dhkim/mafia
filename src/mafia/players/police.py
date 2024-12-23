from typing import Dict

from mafia.players.base_player import BasePlayer
from mafia.utils.enum import ActionType, ContextType


class Police(BasePlayer):

    def take_action(self, context: ContextType) -> ActionType:
        """경찰의 밤 행동 수행"""
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

        result = self._investigate(target)

        self.memory.add_memory({
            "action": "investigate",
            "target": target,
            "result": result,
            "turn": game_state.day_count
        })

        return result

    def _investigate(self, target_player) -> Dict:
        """실제 조사 행동 수행"""
        if not target_player.is_alive:
            return {"success": False, "message": "사망한 플레이어는 조사할 수 없습니다"}

        return {
            "success": True,
            "message": f"{target_player.name}의 역할은 {target_player.role}입니다"
        }
