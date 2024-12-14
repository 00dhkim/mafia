from .base_player import BasePlayer
from ..game.game_state import GameState, GamePhase
from typing import Dict

class Doctor(BasePlayer):
    def __init__(self, name: str):
        super().__init__(name)
        self.role = "의사"
        
    async def take_action(self, game_state: GameState) -> Dict:
        """의사의 밤 행동 수행"""
        if game_state.current_phase != GamePhase.NIGHT:
            return {"success": False, "message": "밤이 아닙니다"}
            
        context = {
            "role": self.role,
            "phase": "밤",
            "alive_players": [p.name for p in game_state.alive_players],
            "memories": self.memory.get_relevant_memories(game_state)
        }
        
        target_name = await self.ai_agent.generate_response(context)
        target = self._validate_and_get_target(
            target_name=target_name,
            candidates=game_state.alive_players,
            name_selector=lambda p: p.name,
            exclude_self=False  # 자신도 치료 가능
        )
        
        if not target:
            return {"success": False, "message": "대상을 찾을 수 없습니다"}
            
        result = self._heal(target)
        
        self.memory.add_memory({
            "action": "heal",
            "target": target,
            "result": result,
            "turn": game_state.day_count
        })
        
        return result
        
    def _heal(self, target_player) -> Dict:
        """실제 치료 행동 수행"""
        if not target_player.is_alive:
            return {"success": False, "message": "이미 사망한 플레이어입니다"}
        
        target_player.is_healed = True
        return {
            "success": True,
            "message": f"{target_player.name}을(를) 치료했습니다"
        }