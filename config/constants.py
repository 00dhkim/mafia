from enum import Enum

class GamePhase(Enum):
    INIT = "INIT"
    DAY = "DAY"
    NIGHT = "NIGHT"
    END = "END"

class Role(Enum):
    MAFIA = "MAFIA"
    DOCTOR = "DOCTOR"
    POLICE = "POLICE"
    CITIZEN = "CITIZEN"

ROLE_DESCRIPTIONS = {
    Role.MAFIA: "밤에 한 명을 죽일 수 있으며, 다른 마피아와 대화할 수 있습니다.",
    Role.DOCTOR: "밤에 한 명을 선택하여 보호할 수 있습니다.",
    Role.POLICE: "밤에 한 명의 직업을 확인할 수 있습니다.",
    Role.CITIZEN: "특별한 능력은 없지만, 토론과 투표에 참여할 수 있습니다."
}