import random
from typing import List
from config.constants import GamePhase
from models.role import Role
from models.player import Player
from systems.chat_system import ChatSystem
from prompts.prompt_manager import PromptManager
class GameManager:
    def __init__(self, player_count: int):
        self.player_count = player_count
        self.players: List[Player] = []
        self.chat_system = ChatSystem()
        self.phase = GamePhase.INIT
        self.day_count = 0

    async def setup_game(self):
        print("\n=== 게임 설정 시작 ===")
        roles = self._assign_roles()
        print(f"역할 분배: {[role.value for role in roles]}")
        for i in range(self.player_count):
            player = Player(f"Player_{i+1}", roles[i])
            player.game = self
            self.players.append(player)
        print(f"플레이어 생성 완료: {[p.name for p in self.players]}")

    def _assign_roles(self) -> List[Role]:
        if self.player_count < 4:  # 최소 4명 필요
            raise ValueError("게임을 시작하기 위해서는 최소 4명의 플레이어가 필요합니다.")
        mafia_count = max(1, self.player_count // 4)
        roles = [Role.MAFIA] * mafia_count
        roles.append(Role.DOCTOR)
        roles.append(Role.POLICE)
        
        citizen_count = self.player_count - len(roles)
        roles.extend([Role.CITIZEN] * citizen_count)
        random.shuffle(roles)
        return roles

    async def run_game(self):
        await self.setup_game()
        while not self._check_game_over():
            await self.run_day_phase()
            if self._check_game_over():
                break
            await self.run_night_phase()
            self.day_count += 1

    async def run_day_phase(self):
        print(f"\n=== 낮 페이즈 시작 (Day {self.day_count + 1}) ===")
        self.phase = GamePhase.DAY
        print("\n--- 토론 시작 ---")
        await self._conduct_discussion()
        print("\n--- 투표 시작 ---")
        voted_player = await self._conduct_voting()
        if voted_player:
            voted_player.is_alive = False
            print(f"처형 결과: {voted_player.name} ({voted_player.role.value})")

    async def run_night_phase(self):
        print(f"\n=== 밤 페이즈 시작 (Night {self.day_count + 1}) ===")
        self.phase = GamePhase.NIGHT
        
        print("\n--- 마피아 행동 ---")
        # 마피아 행동 로직...
        
        print("\n--- 의사 행동 ---")
        protected = await self._conduct_doctor_action()
        
        print("\n--- 경찰 행동 ---")
        await self._conduct_police_action()

    async def _conduct_mafia_action(self, player: Player):
        try:
            chat_history = self.chat_system.get_chat_history("mafia")
            response = await player.generate_response(
                PromptManager.get_mafia_action_prompt(player, chat_history)
            )
            target_name = self._parse_target(response)
            if target_name:
                target = next((p for p in self.players if p.name == target_name 
                             and p.is_alive and p.role != Role.MAFIA), None)
                return target
        except Exception as e:
            print(f"마피아 행동 처리 중 오류 발생: {e}")
        return None

    async def _conduct_doctor_action(self):
        try:
            for player in [p for p in self.players if p.is_alive and p.role == Role.DOCTOR]:
                chat_history = self.chat_system.get_chat_history("public")
                response = await player.generate_response(
                    PromptManager.get_doctor_action_prompt(player, chat_history)
                )
                target_name = self._parse_target(response)
                if target_name:
                    target = next((p for p in self.players if p.name == target_name 
                                 and p.is_alive), None)
                    if target:
                        await self.chat_system.send_message(
                            player,
                            f"{target_name}을(를) 보호하기로 결정했습니다."
                        )
                        return target
        except Exception as e:
            print(f"의사 행동 처리 중 오류 발생: {e}")
        return None

    async def _conduct_police_action(self):
        try:
            for player in [p for p in self.players if p.is_alive and p.role == Role.POLICE]:
                chat_history = self.chat_system.get_chat_history("public")
                response = await player.generate_response(
                    PromptManager.get_police_action_prompt(player, chat_history)
                )
                target_name = self._parse_target(response)
                if target_name:
                    target = next((p for p in self.players if p.name == target_name 
                                 and p.is_alive and p.name != player.name), None)
                    if target:
                        is_mafia = target.role == Role.MAFIA
                        await self.chat_system.send_message(
                            player,
                            f"조사 결과: {target_name}은(는) {'마피아가 맞습니다.' if is_mafia else '마피아가 아닙니다.'}"
                        )
        except Exception as e:
            print(f"경찰 행동 처리 중 오류 발생: {e}")

    def is_mafia_win(self) -> bool:
        # 마피아의 승리 조건을 확인
        mafia_count = len([p for p in self.players if p.is_alive and p.role == Role.MAFIA])
        citizen_count = len([p for p in self.players if p.is_alive and p.role != Role.MAFIA])
        return mafia_count >= citizen_count

    def _check_game_over(self) -> bool:
        alive_players = [p for p in self.players if p.is_alive]
        if not alive_players:
            return True
        mafia_count = len([p for p in alive_players if p.role == Role.MAFIA])
        citizen_count = len([p for p in alive_players if p.role != Role.MAFIA])
        
        # 모든 마피아가 죽었거나, 마피아 수가 시민 수 이상이면 게임 종료
        return mafia_count == 0 or mafia_count >= citizen_count

    async def _conduct_discussion(self):
        # 토론 진행 로직
        for player in [p for p in self.players if p.is_alive]:
            chat_history = self.chat_system.get_chat_history("public")
            response = await player.generate_response(
                PromptManager.get_discussion_prompt(player, chat_history)
            )
            await self.chat_system.send_message(player, response)

    async def _conduct_voting(self):
        votes = {}
        alive_players = [p for p in self.players if p.is_alive]
        
        # 투표 진행
        for player in alive_players:
            try:
                chat_history = self.chat_system.get_chat_history("public")
                response = await player.generate_response(
                    PromptManager.get_voting_prompt(player, chat_history)
                )
                voted_player = self._parse_vote(response)
                if voted_player and voted_player.is_alive:
                    votes[voted_player] = votes.get(voted_player, 0) + 1
            except Exception as e:
                print(f"투표 처리 중 오류 발생: {e}")
                continue
        
        # 최다 득표자 선정 (동률일 경우 랜덤 선택)
        if votes:
            max_votes = max(votes.values())
            potential_targets = [k for k, v in votes.items() if v == max_votes]
            target = random.choice(potential_targets)
            await self.chat_system.send_message(
                None,
                f"투표 결과: {', '.join([f'{p.name}: {votes[p]}표' for p in votes])}"
            )
            return target
        return None

    def _parse_target(self, response: str) -> str:
        try:
            if not response or "대상:" not in response:
                return None
            target = response.split("대상:")[1].split("\n")[0].strip()
            return target if target else None
        except Exception:
            return None

    def _parse_vote(self, response: str) -> Player:
        try:
            if not response or "투표 대상:" not in response:
                return None
            player_name = response.split("투표 대상:")[1].split("\n")[0].strip()
            return next((p for p in self.players if p.name == player_name and p.is_alive), None)
        except Exception:
            return None