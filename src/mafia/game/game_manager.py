import random
from typing import List, Dict, Literal, Optional

from mafia.ai.memory_manager import MemoryType
from mafia.players.base_player import BasePlayer
from mafia.players.citizen import Citizen
from mafia.players.doctor import Doctor
from mafia.players.police import Police
from mafia.players.mafia import Mafia
from mafia.utils.config import game_config
from mafia.utils.enum import ActionType, ContextType, GamePhase, GameStateType, Role, names
from mafia.utils.logger import GameLogger


class GameManager:
    """게임 진행 관리자
    
    PRD 요구사항:
    - 턴 기반 게임 진행
    - 게임 상태 관리
    - 플레이어 관리
    
    주요 기능:
    1. 게임 상태 관리
       - 생존/사망 플레이어 관리
       - 현재 게임 단계 추적
       - 투표 결과 관리
       - 승리 조건 검사
       
    2. 턴 진행 관리
       - 낮/밤 페이즈 진행
       - 턴 전환
       - 페이즈별 행동 순서 조정
       
    3. 대화 관리
       - 대화 참여자 관리
       - 대화 순서 조정
    """
    def __init__(self):
        # 게임 상태 관련 속성들
        self.current_phase: GamePhase = GamePhase.DAY_CONVERSATION
        self.day_count: int = 1
        self.alive_players: List[BasePlayer] = []
        self.dead_players: List[BasePlayer] = []
        self.vote_results: Dict[BasePlayer, BasePlayer] = {}  # voter_name: voted_name
        self.last_killed_player: Optional[BasePlayer] = None
        self.last_healed_player: Optional[BasePlayer] = None
        self.last_investigated_player: Optional[BasePlayer] = None
        self.current_speaker = None
        self.logger = GameLogger()
        self.announcer = BasePlayer("사회자", -1, None)  # pylint: disable=E0110

    def initialize_game(self):
        """게임 초기화 및 역할 분배"""
        # 설정에서 역할 정보 가져오기
        roles = game_config.get_config("roles")

        # 플레이어 생성
        players: List[BasePlayer] = []
        roles = game_config.get_config("roles")
        roles = list(roles.items())
        random.shuffle(roles)

        idx = 0
        for role, count in roles:
            for i in range(count):
                if role == "citizen":
                    player = Citizen(names[idx], idx, Role.CITIZEN)
                elif role == "doctor":
                    player = Doctor(names[idx], idx, Role.DOCTOR)
                elif role == "police":
                    player = Police(names[idx], idx, Role.POLICE)
                elif role == "mafia":
                    player = Mafia(names[idx], idx, Role.MAFIA)
                else:
                    raise ValueError(f"잘못된 역할입니다: {role}")
                players.append(player)
                idx += 1

        assert idx == len(players), f"플레이어 수가 일치하지 않습니다. {idx} != {len(players)}"
        assert len(set([p.name for p in players])) == len(
            players
        ), f"중복된 이름이 있습니다: {[p.name for p in players]}"

        # 게임 상태 초기화
        self.alive_players = players
        self.dead_players = []

    def spin(self):
        """게임 메인 루프 실행"""
        while True:
            # 1번 페이즈 - 낮 대화
            self._update_phase(GamePhase.DAY_CONVERSATION)
            self.run_day_conversation_phase()

            # 2번 페이즈 - 낮 추리
            self._update_phase(GamePhase.DAY_REASONING)
            self.run_day_reasoning_phase()

            # 3번 페이즈 - 낮 투표
            self._update_phase(GamePhase.DAY_VOTE)
            self.run_day_vote_phase()

            # 시민팀 승리 조건 확인
            game_result = self._is_game_over()
            if game_result["is_over"]:
                break

            # 4번 페이즈 - 밤 행동
            self._update_phase(GamePhase.NIGHT_ACTION)
            self.run_night_phase()

            # 마피아팀 승리 조건 확인
            game_result = self._is_game_over()
            if game_result["is_over"]:
                break

        print("******************************************")
        print(f"게임 종료! 승리 팀: {game_result['winner']}")
        print("******************************************")

    def _is_game_over(self) -> Dict[str, any]:
        """게임 종료 조건 확인"""
        mafia_count = sum(1 for p in self.alive_players if p.role == Role.MAFIA)
        citizen_count = sum(1 for p in self.alive_players if p.role != Role.MAFIA)

        if mafia_count == 0:
            return {"is_over": True, "winner": "시민"}
        if mafia_count >= citizen_count:
            return {"is_over": True, "winner": "마피아"}
        return {"is_over": False, "winner": None}

    def _update_phase(self, phase: GamePhase = None):
        """게임 상태 업데이트"""
        if phase:
            self.current_phase = phase
        if phase == GamePhase.DAY_CONVERSATION:
            self.day_count += 1
            self.vote_results.clear()
            self.last_killed_player = None
            self.last_healed_player = None
            self.last_investigated_player = None

        self.announce(f"현재 게임 상태: {self.day_count}일차 {self.current_phase} 페이즈")

    def _handle_death(self, player: BasePlayer, cause: Literal["마피아", "투표"]) -> str:
        """플레이어 사망 처리"""
        assert player is not None, "플레이어가 지정되지 않았습니다."
        assert player.is_alive, f"이미 사망한 플레이어입니다: {player.name}"
        assert player in self.alive_players, f"존재하지 않는 플레이어입니다: {player.name}"

        player.is_alive = False
        self.alive_players.remove(player)
        self.dead_players.append(player)

        return f"{player.name}이(가) {cause}로 인해 사망했습니다"

    def run_day_conversation_phase(self):
        """낮 페이즈 진행
        1. 생존자 확인 및 사망자 발표
        2. 플레이어 간 대화
        """

        # 1. 생존자 확인 및 사망자 발표
        content = "밤동안 아무 일도 일어나지 않았습니다."
        if self.day_count == 1:
            content = "첫날 낮이 밝았습니다."
        elif self.last_killed_player and self.last_killed_player != self.last_healed_player:
            content = self._handle_death(self.last_killed_player, "마피아")
        elif self.last_killed_player and self.last_killed_player == self.last_healed_player:
            content = f"{self.last_healed_player.name}이(가) 마피아의 공격을 생존했습니다."

        self.announce(content)

        # 2. 플레이어 간 대화
        conversation_round = 2  # 낮동안 각자는 두번씩 발언
        for player in self.alive_players * conversation_round:
            self.current_speaker = player
            context = self.get_context(player)
            conversation = player.generate_conversation(context)

            for listener in self.alive_players:
                listener.receive_public_message(conversation)

    def run_day_reasoning_phase(self):
        """낮 추리 페이즈 진행
        - known_roles: {player: role}  # 확인된 다른 플레이어의 역할
        - suspicious_players: List  # 의심스러운 플레이어 목록
        - trusted_players: List  # 신뢰할 수 있는 플레이어 목록
        """
        raise NotImplementedError

    def run_day_vote_phase(self):
        """투표 진행 및 결과 처리"""
        # 각 플레이어의 투표 수집
        for voter in self.alive_players:
            context = self.get_context(voter)
            vote_action = voter.take_action(context)
            assert vote_action.get("type") == "vote", f"투표 행동이 아닙니다: {vote_action}"

            if vote_action["target"] in [p.name for p in self.alive_players]:
                self.vote_results[voter] = vote_action["target"]
            else:
                raise ValueError(f"유효하지 않은 투표 대상: {vote_action['target']}")
        self.logger.info(f"투표 결과: {self.vote_results}")

        # 투표 결과 집계
        assert self.vote_results, "투표 결과가 없습니다."
        vote_count: Dict[BasePlayer, int] = {}
        for voted in self.vote_results.values():
            vote_count[voted] = vote_count.get(voted, 0) + 1

        # 최다 득표자 처리
        assert vote_count, "투표 결과가 없습니다."
        max_votes = max(vote_count.values())
        executed_players = [name for name, votes in vote_count.items() if votes == max_votes]

        if len(executed_players) == 1:
            executed_player = next(
                p for p in self.alive_players if p.name == executed_players[0]
            )
            content = self._handle_death(executed_player, "투표")
            self.announce(content)
        else:
            self.announce("최다 득표자가 동률로 인해 처형되지 않았습니다.")

    def run_night_phase(self):
        """밤 페이즈 진행
        1. 마피아 행동
        2. 의사 행동
        3. 경찰 행동
        """

        # 역할별 행동 순서 정의
        role_order = [Role.MAFIA, Role.DOCTOR, Role.POLICE]

        # 역할 순서대로 행동 실행
        actions: Dict[BasePlayer, ActionType] = {}
        for role in role_order:
            for player in self.alive_players:
                if player.role == role:
                    context = self.get_context(player)
                    action = player.take_action(context)
                    assert action.get("type") == "skill", f"스킬 행동이 아닙니다: {action}"
                    actions[player] = action

        # 행동 결과 처리
        for player, action in actions.items():
            private_memory = self._resolve_night_action(player, action)
            player.memory_manager.add_memory(private_memory)
            self.logger.info(
                f"사회자 -> {player.name}({player.role}): {private_memory['content']}"
            )

    def _resolve_night_action(self, actor: BasePlayer, action: ActionType) -> MemoryType:
        """밤 행동 결과 처리

        Args:
            actor: 행동을 수행하는 플레이어
            action: 행동 정보

        Returns:
            MemoryType: 개인 메모리
        """
        target = action.get("target")

        assert action is not None, "행동이 지정되지 않았습니다."
        assert target is not None, "대상이 지정되지 않았습니다."
        assert actor.is_alive, f"사망한 플레이어는 행동할 수 없습니다: {actor.name}"
        assert actor in self.alive_players, f"존재하지 않는 플레이어입니다: {actor.name}"
        assert target.is_alive, f"사망한 플레이어는 대상이 될 수 없습니다: {target.name}"
        assert target in self.alive_players, f"존재하지 않는 대상입니다: {target.name}"

        content = ""

        if actor.role == "마피아":
            self.last_killed_player = target
            content = f"{target.name}을(를) 공격했습니다."
        elif actor.role == "의사":
            self.last_healed_player = target
            content = f"{target.name}을(를) 치료했습니다."
        elif actor.role == "경찰":
            self.last_investigated_player = target
            if target.role == "마피아":
                content = f"{target.name}은(는) 마피아입니다."
            else:
                content = f"{target.name}은(는) 마피아가 아닙니다."

        private_memory = MemoryType(
            day=self.day_count,
            phase=self.current_phase,
            speaker=self.announcer,
            content=content,
        )

        return private_memory

    @property
    def game_state(self) -> GameStateType:
        """게임 상태 반환"""

        assert all(
            p.name in [p.name for p in self.alive_players]
            or p.name in [p.name for p in self.dead_players]
            for p in self.alive_players + self.dead_players
        ), f"플레이어 목록에 중복이 있습니다. alive: {self.alive_players}, dead: {self.dead_players}"

        game_state = GameStateType(
            phase=self.current_phase,
            day_count=self.day_count,
            alive_players=self.alive_players,
            dead_players=self.dead_players,
            vote_results=self.vote_results,
        )
        return game_state

    def announce(self, content: str):
        """사회자 발언 공지"""
        info = MemoryType(
            day=self.day_count,
            phase=self.current_phase,
            speaker=self.announcer,
            content=content,
        )
        for listener in self.alive_players:
            listener.receive_public_message(info)
        # for listener in self.dead_players:
        #     listener.receive_public_message(info)
        self.logger.info(f"[공지] 사회자: {content}")

    def get_context(self, player: BasePlayer) -> ContextType:
        """현재 게임 상태 및 정보를 반환"""
        return ContextType(
            day_count=self.day_count,
            phase=self.current_phase,
            alive_players=self.alive_players,
            memories=player.memory_manager.get_recent_memories(self.day_count),
        )
