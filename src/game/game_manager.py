from typing import List, Dict, Optional
from ai.llm_agent import LLMAgent
from players.base_player import BasePlayer
from players.citizen import Citizen
from players.doctor import Doctor
from players.police import Police
from players.mafia import Mafia
from utils.config import game_config
from ai.memory_manager import MemoryType
import random
from utils.enum import ContextType, GamePhase, GameStateType, Role, names
from utils.logger import GameLogger


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
        self.vote_results: Dict[str, str] = {}  # voter_name: voted_name
        self.last_killed_player: Optional[BasePlayer] = None
        self.last_healed_player: Optional[BasePlayer] = None
        self.last_investigated_player: Optional[BasePlayer] = None
        self.current_speaker = None
        self.logger = GameLogger()

    def initialize_game(self):
        """게임 초기화 및 역할 분배"""
        # 설정에서 역할 정보 가져오기
        roles = game_config.get_config("roles")

        # 플레이어 생성
        players = []
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

        # 게임 상태 초기화
        self.alive_players = players
        self.dead_players = []

    def is_game_over(self) -> Dict[str, any]:
        """게임 종료 조건 확인"""
        mafia_count = sum(1 for p in self.alive_players if p.role == "마피아")
        citizen_count = sum(1 for p in self.alive_players if p.role != "마피아")

        if mafia_count == 0:
            return {"is_over": True, "winner": "시민"}
        if mafia_count >= citizen_count:
            return {"is_over": True, "winner": "마피아"}
        return {"is_over": False, "winner": None}

    def update_phase(self, phase: GamePhase = None):
        """게임 상태 업데이트"""
        if phase:
            self.current_phase = phase
        if phase == GamePhase.DAY_CONVERSATION:
            self.day_count += 1
            self.vote_results.clear()
            self.last_killed_player = None
            self.last_healed_player = None
            self.last_investigated_player = None

    def handle_death(self, player: BasePlayer):
        """플레이어 사망 처리"""
        try:
            assert player is not None, "플레이어가 지정되지 않았습니다."

            if not player.is_alive:
                self.logger.warning(f"이미 사망한 플레이어입니다: {player.name}")
                return

            if player not in self.alive_players:
                raise ValueError(f"존재하지 않는 플레이어입니다: {player.name}")

            player.is_alive = False
            self.alive_players.remove(player)
            self.dead_players.append(player)

            self.broadcast_death(player.name)

        except Exception as e:
            self.logger.error(f"사망 처리 중 오류 발생: {str(e)}")

    def run_game(self):
        """게임 메인 루프 실행"""
        while True:
            # 승리 조건 확인
            game_result = self.is_game_over()
            if game_result["is_over"]:
                print(f"게임 종료! 승리 팀: {game_result['winner']}")
                break

            # 낮 페이즈
            self.run_day_phase()

            # 승리 조건 재확인
            game_result = self.is_game_over()
            if game_result["is_over"]:
                print(f"게임 종료! 승리 팀: {game_result['winner']}")
                break

            # 밤 페이즈
            self.run_night_phase()

    def broadcast_death(self, victim: str, cause: str = "처형"):
        """사망 정보 공개"""
        death_info = {
            "type": MemoryType.DEATH,
            "content": f"{victim}이(가) {cause}로 사망했습니다",
            "turn": self.day_count,
            "phase": self.current_phase,
            "players": [victim],
            "source": "public_announcement"
        }
        for player in self.alive_players:
            player.receive_public_info(death_info)

    def handle_night_action(self, actor: BasePlayer, action: Dict):
        """밤 행동 처리
        
        Args:
            actor: 행동을 수행하는 플레이어
            action: {
                "type": str,     # 행동 유형 (마피아/의사/경찰)
                "target": str,   # 대상 플레이어 이름
                "content": str   # 행동 설명
            }
        """
        try:
            assert action is not None, "행동이 지정되지 않았습니다."
            assert isinstance(action, dict), "잘못된 행동 형식입니다."

            result = self._resolve_night_action(actor, action)

            if isinstance(actor, LLMAgent):
                try:
                    memory = MemoryType(
                        type=MemoryType.NIGHT_ACTION,
                        content=result["message"],
                        turn=self.day_count,
                        phase=GamePhase.NIGHT_ACTION,
                        players=[actor.player_id, action["target"]],
                        source="direct_experience",
                    )
                    actor.memory_manager.add_memory(memory)
                except Exception as e:
                    self.logger.error(f"메모리 저장 중 오류 발생: {str(e)}")

        except Exception as e:
            self.logger.error(f"밤 행동 처리 중 오류 발생 - {actor.name}: {str(e)}")
            # 오류 발생 시 기본 행동 수행
            self._handle_fallback_night_action(actor)

    def handle_vote(self, voter: BasePlayer, target: BasePlayer):
        """투표 처리"""
        # 투표는 공개 정보
        vote_info = {
            "type": MemoryType.VOTE,
            "content": f"{voter.player_id}가 {target.player_id}에게 투표했습니다",
            "turn": self.day_count,
            "phase": GamePhase.DAY_VOTE,
            "players": [voter.player_id, target.player_id],
            "source": "public_announcement"
        }
        # 모든 플레이어에게 전달
        for player in self.alive_players:
            player.receive_public_info(vote_info)

    def handle_conversation(self, context: ContextType):
        """대화 진행 관리"""
        # 생존한 플레이어들의 대화 순서 관리
        for player in self.alive_players:
            self.current_speaker = player
            player.generate_conversation(context)

    def run_day_phase(self):
        """낮 페이즈 진행
        1. 생존자 확인 및 사망자 발표
        2. 플레이어 간 대화
        3. 투표 진행
        """
        self.update_phase(GamePhase.DAY_CONVERSATION)

        # 1. 생존자 확인 및 사망자 발표
        if self.last_killed_player:
            if not self.last_healed_player or \
               self.last_killed_player != self.last_healed_player:
                self.handle_death(self.last_killed_player)

        # 2. 플레이어 간 대화
        context = {
            "phase": self.current_phase,
            "day_count": self.day_count,
            "alive_players": [p.name for p in self.alive_players],
            "dead_players": [p.name for p in self.dead_players]
        }
        self.handle_conversation(context)

        # 3. 투표 진행
        self.handle_voting()

    def run_night_phase(self):
        """밤 페이즈 진행
        1. 마피아 행동
        2. 의사 행동
        3. 경찰 행동
        """
        self.update_phase(GamePhase.NIGHT_ACTION)

        context = {
            "phase": self.current_phase,
            "day_count": self.day_count,
            "alive_players": [p.name for p in self.alive_players]
        }

        # 역할별 행동 순서 정의
        role_order = ["마피아", "의사", "경찰"]

        # 역할 순서대로 행동 실행
        for role in role_order:
            for player in self.alive_players:
                if player.role == role:
                    action = player.take_action(context)
                    self.handle_night_action(player, action)

    def handle_voting(self):
        """투표 진행 및 결과 처리"""
        try:
            self.update_phase(GamePhase.DAY_VOTE)

            # 투표 진행
            context = {
                "phase": GamePhase.DAY_VOTE,
                "day_count": self.day_count,
                "alive_players": [p.name for p in self.alive_players]
            }

            # 각 플레이어의 투표 수집
            for voter in self.alive_players:
                try:
                    vote_action = voter.take_action(context)
                    if vote_action and vote_action.get("target"):
                        if vote_action["target"] in [p.name for p in self.alive_players]:
                            self.vote_results[voter.name] = vote_action["target"]
                        else:
                            raise ValueError(f"유효하지 않은 투표 대상: {vote_action['target']}")
                except Exception as e:
                    self.logger.error(f"투표 처리 중 오류 발생 - {voter.name}: {str(e)}")
                    # 오류 발생 시 랜덤 투표
                    valid_targets = [p.name for p in self.alive_players if p.name != voter.name]
                    if valid_targets:
                        self.vote_results[voter.name] = random.choice(valid_targets)

            # 투표 결과 집계
            if not self.vote_results:
                self.logger.warning("유효한 투표 결과가 없습니다.")
                return

            vote_count: Dict[str, int] = {}
            for voted_name in self.vote_results.values():
                vote_count[voted_name] = vote_count.get(voted_name, 0) + 1

            # 최다 득표자 처리
            if vote_count:
                max_votes = max(vote_count.values())
                executed_players = [name for name, votes in vote_count.items() 
                                  if votes == max_votes]

                if len(executed_players) == 1:
                    executed_player = next(p for p in self.alive_players 
                                        if p.name == executed_players[0])
                    self.handle_death(executed_player)
                else:
                    self.logger.info(f"동률 발생으로 처형 무산: {executed_players}")

        except Exception as e:
            self.logger.error(f"투표 진행 중 치명적 오류 발생: {str(e)}")

    def _resolve_night_action(self, actor: BasePlayer, action: Dict) -> Dict:
        """밤 행동 결과 처리
        
        Args:
            actor: 행동을 수행하는 플레이어
            action: {
                "type": str,     # 행동 유형 (마피아/의사/경찰)
                "target": str,   # 대상 플레이어 이름
                "content": str   # 행동 설명
            }
        
        Returns:
            Dict: {
                "success": bool,  # 행동 성공 여부
                "message": str    # 결과 메시지
            }
        """
        target_name = action.get("target")
        target = next((p for p in self.alive_players if p.name == target_name), None)

        if not target:
            return {"success": False, "message": "대상을 찾을 수 없습니다."}

        result = {"success": True}

        if actor.role == "마피아":
            self.last_killed_player = target
            result["message"] = f"{target_name}을(를) 공격했습니다."
        elif actor.role == "의사":
            self.last_healed_player = target
            result["message"] = f"{target_name}을(를) 치료했습니다."
        elif actor.role == "경찰":
            self.last_investigated_player = target
            is_mafia = target.role == "마피아"
            result["message"] = f"{target_name}은(는) {'마피아가 맞습니다.' if is_mafia else '마피아가 아닙니다.'}"

        return result

    def get_game_state(self) -> GameStateType:
        """게임 상태 반환"""

        assert all(
            p.name in [p.name for p in self.alive_players]
            or p.name in [p.name for p in self.dead_players]
            for p in self.alive_players + self.dead_players
        ), f"플레이어 목록에 중복이 있습니다. alive: {self.alive_players}, dead: {self.dead_players}"

        game_state = GameStateType(
            phase=self.current_phase,
            day_count=self.day_count,
            alive_players=[p.name for p in self.alive_players],
            dead_players=[p.name for p in self.dead_players],
            vote_results=self.vote_results,
        )
        return game_state
