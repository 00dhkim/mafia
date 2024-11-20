from typing import List
from datetime import datetime
from models.player import Player
from models.role import Role

class ChatMessage:
    def __init__(self, sender: str, content: str, chat_type: str):
        self.sender = sender
        self.content = content
        self.timestamp = datetime.now()
        self.chat_type = chat_type

class ChatSystem:
    def __init__(self):
        self.public_chat: List[ChatMessage] = []
        self.mafia_chat: List[ChatMessage] = []
        self.dead_chat: List[ChatMessage] = []

    async def send_message(self, player: Player, content: str, chat_type: str = "public"):
        sender_name = player.name if player else "시스템"
        print(f"\n[{chat_type.upper()} 채팅] {sender_name}: {content}")
        message = ChatMessage(sender_name, content, chat_type)
        if chat_type == "public":
            self.public_chat.append(message)
        elif chat_type == "mafia" and player and player.role == Role.MAFIA:
            self.mafia_chat.append(message)
        elif chat_type == "dead" and player and not player.is_alive:
            self.dead_chat.append(message)

    def get_chat_history(self, chat_type: str) -> List[ChatMessage]:
        if chat_type == "public":
            return self.public_chat
        elif chat_type == "mafia":
            return self.mafia_chat
        elif chat_type == "dead":
            return self.dead_chat
        return [] 