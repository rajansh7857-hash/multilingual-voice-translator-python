import json
import time
import uuid
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket
from backend.translator import translate_for_multiple_languages, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# Distinct avatar colors for visual differentiation
AVATAR_COLORS = [
    "#3B82F6", "#10B981", "#8B5CF6", "#F59E0B", "#EC4899",
    "#6366F1", "#14B8A6", "#F97316", "#06B6D4", "#84CC16"
]

class Participant:
    def __init__(self, user_id: str, name: str, language: str, websocket: WebSocket, avatar_color: str):
        self.user_id = user_id
        self.name = name
        self.language = language
        self.websocket = websocket
        self.avatar_color = avatar_color
        self.joined_at = time.time()

    def to_dict(self) -> dict:
        lang_meta = SUPPORTED_LANGUAGES.get(self.language, {"name": self.language, "flag": "🌐"})
        return {
            "user_id": self.user_id,
            "name": self.name,
            "language": self.language,
            "language_name": lang_meta.get("name", self.language),
            "flag": lang_meta.get("flag", "🌐"),
            "avatar_color": self.avatar_color
        }


class Room:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.participants: Dict[str, Participant] = {}
        self.messages: List[dict] = []
        self.color_index = 0

    def add_participant(self, user_id: str, name: str, language: str, websocket: WebSocket) -> Participant:
        color = AVATAR_COLORS[self.color_index % len(AVATAR_COLORS)]
        self.color_index += 1
        participant = Participant(user_id, name, language, websocket, color)
        self.participants[user_id] = participant
        return participant

    def remove_participant(self, user_id: str) -> Optional[Participant]:
        return self.participants.pop(user_id, None)

    def get_target_languages(self) -> Set[str]:
        """Get all distinct languages used by participants in the room."""
        return {p.language for p in self.participants.values()}

    def get_participants_list(self) -> List[dict]:
        return [p.to_dict() for p in self.participants.values()]


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def get_or_create_room(self, room_id: str) -> Room:
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id)
        return self.rooms[room_id]

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id)

    async def broadcast_to_room(self, room_id: str, message_dict: dict, exclude_user_id: Optional[str] = None):
        room = self.get_room(room_id)
        if not room:
            return

        dead_connections = []
        text_data = json.dumps(message_dict)

        for user_id, participant in room.participants.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            try:
                await participant.websocket.send_text(text_data)
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                dead_connections.append(user_id)

        for dead_user in dead_connections:
            self.remove_participant(room_id, dead_user)

    def remove_participant(self, room_id: str, user_id: str):
        room = self.get_room(room_id)
        if room:
            room.remove_participant(user_id)
            if not room.participants:
                self.rooms.pop(room_id, None)

    async def handle_speech_broadcast(
        self,
        room_id: str,
        sender_id: str,
        original_text: str,
        source_lang: str,
        target_lang: Optional[str] = None
    ):
        room = self.get_room(room_id)
        if not room or sender_id not in room.participants:
            return

        sender = room.participants[sender_id]
        clean_text = original_text.strip()
        if not clean_text:
            return

        # 1. Determine all unique target languages in the room
        target_languages = room.get_target_languages()
        target_languages.add(source_lang)  # Ensure sender's language is present
        if target_lang:
            target_languages.add(target_lang)

        # 2. Perform concurrent translation for each unique language
        translations = await translate_for_multiple_languages(clean_text, source_lang, target_languages)

        msg_id = f"msg_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        timestamp = time.strftime("%H:%M:%S")

        dead_connections = []
        # 3. Deliver customized translated message to each participant
        for user_id, participant in room.participants.items():
            is_self = (user_id == sender_id)
            
            # For the sender, if a target_lang was specified, use that translation so the sender sees the translation!
            if is_self and target_lang and target_lang != source_lang:
                user_target_lang = target_lang
            else:
                user_target_lang = participant.language

            translated_text = translations.get(user_target_lang, clean_text)
            
            payload = {
                "type": "speech_message",
                "id": msg_id,
                "sender_id": sender.user_id,
                "sender_name": sender.name,
                "sender_lang": source_lang,
                "sender_color": sender.avatar_color,
                "original_text": clean_text,
                "translated_text": translated_text,
                "recipient_lang": user_target_lang,
                "translations": translations,
                "is_self": is_self,
                "timestamp": timestamp
            }
            try:
                await participant.websocket.send_text(json.dumps(payload))
            except Exception as e:
                logger.warning(f"Error sending speech message to {user_id}: {e}")
                dead_connections.append(user_id)

        for dead_user in dead_connections:
            self.remove_participant(room_id, dead_user)
