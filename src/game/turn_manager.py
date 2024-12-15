from typing import List, Dict, Optional
from .game_state import GameState, GamePhase
from ..players.base_player import BasePlayer

class TurnManager:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        
    async def run_day_phase(self):
        """낮 페이즈 진행"""
        self.game_state.update_state(GamePhase.DAY)
        
        # 1. 생존자 확인 및 사망자 발표
        if self.game_state.last_killed_player:
            if not self.game_state.last_healed_player or \
               self.game_state.last_killed_player != self.game_state.last_healed_player:
                self._handle_death(self.game_state.last_killed_player)
        
        # 2. 플레이어 간 대화
        for player in self.game_state.alive_players:
            # 낮에는 모든 플레이어가 대화에 참여
            player.discuss(self.game_state)
            
        # 3. 투표 진행
        self._handle_voting()
        
    def run_night_phase(self):
        """밤 페이즈 진행"""
        self.game_state.update_state(GamePhase.NIGHT)
        
        # 1. 마피아 행동
        for player in self.game_state.alive_players:
            if player.role == "마피아":
                player.take_action(self.game_state)
                
        # 2. 의사 행동
        for player in self.game_state.alive_players:
            if player.role == "의사":
                player.take_action(self.game_state)
                
        # 3. 경찰 행동
        for player in self.game_state.alive_players:
            if player.role == "경찰":
                player.take_action(self.game_state)
    
    def _handle_voting(self):
        """투표 진행 및 결과 처리"""
        self.game_state.update_state(GamePhase.VOTING)
        
        # 투표 진행
        for player in self.game_state.alive_players:
            vote = player.vote(self.game_state.alive_players)
            self.game_state.vote_results[player.name] = vote
            
        # 투표 결과 집계
        vote_count: Dict[str, int] = {}
        for voted_name in self.game_state.vote_results.values():
            vote_count[voted_name] = vote_count.get(voted_name, 0) + 1
            
        # 최다 득표자 처리
        if vote_count:
            max_votes = max(vote_count.values())
            executed_players = [name for name, votes in vote_count.items() if votes == max_votes]
            
            if len(executed_players) == 1:
                executed_player = next(p for p in self.game_state.alive_players 
                                    if p.name == executed_players[0])
                self._handle_death(executed_player)
                
    def _handle_death(self, player: BasePlayer):
        """플레이어 사망 처리"""
        player.is_alive = False
        self.game_state.alive_players.remove(player)
        self.game_state.dead_players.append(player)