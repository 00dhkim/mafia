from enum import Enum

class Role(Enum):
    MAFIA = "마피아"
    CITIZEN = "시민"
    DOCTOR = "의사"
    POLICE = "경찰"

ROLE_DESCRIPTIONS = {
    Role.MAFIA: "밤에 한 명을 죽일 수 있습니다",
    Role.CITIZEN: "특별한 능력이 없습니다",
    Role.DOCTOR: "밤에 한 명을 보호할 수 있습니다",
    Role.POLICE: "밤에 한 명의 역할을 확인할 수 있습니다"
} 