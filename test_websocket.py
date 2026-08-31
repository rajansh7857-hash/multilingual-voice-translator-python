import asyncio
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.main import app

def test_websocket_flow():
    client = TestClient(app)
    
    # Simulate two participants in room "sync-room"
    # User 1: Alice (English)
    # User 2: Carlos (Spanish)
    
    with client.websocket_connect("/ws/sync-room/usr_alice?name=Alice&language=en") as ws_alice:
        # Receive join room_update
        msg_alice = json.loads(ws_alice.receive_text())
        assert msg_alice["type"] == "room_update"
        print("✓ Alice joined 'sync-room' (English)")

        with client.websocket_connect("/ws/sync-room/usr_carlos?name=Carlos&language=es") as ws_carlos:
            # Carlos gets room update
            msg_carlos = json.loads(ws_carlos.receive_text())
            assert msg_carlos["type"] == "room_update"
            print("✓ Carlos joined 'sync-room' (Spanish)")

            # Alice also receives room_update about Carlos joining
            update_for_alice = json.loads(ws_alice.receive_text())
            assert update_for_alice["type"] == "room_update"
            print("✓ Alice received room update notification")

            # Alice speaks in English: "Good morning team, let's start the presentation."
            ws_alice.send_text(json.dumps({
                "type": "speech",
                "text": "Good morning team, let's start the presentation.",
                "source_lang": "en"
            }))

            # Alice receives her self-message in English
            alice_echo = json.loads(ws_alice.receive_text())
            print(f"✓ Alice sees original/translated: '{alice_echo['translated_text']}'")

            # Carlos receives the speech translated into Spanish in real-time
            carlos_received = json.loads(ws_carlos.receive_text())
            assert carlos_received["type"] == "speech_message"
            assert carlos_received["sender_name"] == "Alice"
            assert carlos_received["recipient_lang"] == "es"
            print(f"✓ Carlos received translated Spanish audio/text: '{carlos_received['translated_text']}'")

    print("\n[SUCCESS] WebSocket multi-language translation flow verified!")

if __name__ == "__main__":
    test_websocket_flow()
