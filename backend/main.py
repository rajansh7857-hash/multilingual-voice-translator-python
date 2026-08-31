import os
import json
import logging
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.translator import SUPPORTED_LANGUAGES, translate_text
from backend.rooms import RoomManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Multilingual Voice Translator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

room_manager = RoomManager()

# --- REST Endpoints ---

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

@app.get("/api/languages")
async def get_languages():
    """Return all supported languages with codes, names, flags and locales."""
    return {
        "status": "success",
        "languages": [
            {"code": code, **meta}
            for code, meta in SUPPORTED_LANGUAGES.items()
        ]
    }

@app.post("/api/translate")
async def api_translate(req: TranslationRequest):
    """Translate text directly via HTTP."""
    if not req.text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    translated = await translate_text(req.text, req.source_lang, req.target_lang)
    return {
        "original": req.text,
        "source_lang": req.source_lang,
        "target_lang": req.target_lang,
        "translated": translated
    }

@app.get("/api/rooms/{room_id}")
async def get_room_details(room_id: str):
    """Get current participants in a room."""
    room = room_manager.get_room(room_id)
    if not room:
        return {"room_id": room_id, "participants": []}
    return {"room_id": room_id, "participants": room.get_participants_list()}

# --- WebSocket Endpoint for Real-time Voice / Text Stream ---

@app.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: str,
    name: Optional[str] = Query(None),
    language: Optional[str] = Query("en")
):
    await websocket.accept()
    room = room_manager.get_or_create_room(room_id)
    participant_name = name or f"User_{user_id[:4]}"
    user_language = language or "en"

    participant = room.add_participant(user_id, participant_name, user_language, websocket)
    logger.info(f"User '{participant_name}' ({user_id}) joined room '{room_id}' with language '{user_language}'")

    # Notify everyone in room about updated participant list
    await room_manager.broadcast_to_room(room_id, {
        "type": "room_update",
        "participants": room.get_participants_list(),
        "system_message": f"{participant_name} joined the room ({SUPPORTED_LANGUAGES.get(user_language, {}).get('name', user_language)})"
    })

    try:
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            action = data.get("type")

            if action == "speech" or action == "text_message":
                text = data.get("text", "").strip()
                src_lang = data.get("source_lang", participant.language)
                if text:
                    await room_manager.handle_speech_broadcast(room_id, user_id, text, src_lang)

            elif action == "speaking_state":
                is_speaking = bool(data.get("is_speaking", False))
                await room_manager.broadcast_to_room(room_id, {
                    "type": "user_speaking",
                    "user_id": user_id,
                    "name": participant.name,
                    "is_speaking": is_speaking
                }, exclude_user_id=user_id)

            elif action == "update_profile":
                new_lang = data.get("language")
                new_name = data.get("name")
                if new_lang and new_lang in SUPPORTED_LANGUAGES:
                    participant.language = new_lang
                if new_name and new_name.strip():
                    participant.name = new_name.strip()
                
                await room_manager.broadcast_to_room(room_id, {
                    "type": "room_update",
                    "participants": room.get_participants_list(),
                    "system_message": f"{participant.name} updated their settings."
                })

            elif action == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        logger.info(f"User '{participant.name}' ({user_id}) disconnected from room '{room_id}'")
        room.remove_participant(user_id)
        if not room.participants:
            room_manager.rooms.pop(room_id, None)
        else:
            await room_manager.broadcast_to_room(room_id, {
                "type": "room_update",
                "participants": room.get_participants_list(),
                "system_message": f"{participant.name} left the room."
            })
    except Exception as e:
        logger.error(f"WebSocket error for {user_id} in {room_id}: {e}")
        room_manager.remove_participant(room_id, user_id)


# --- Serve Frontend Static Files ---
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(frontend_path, "index.html"))
