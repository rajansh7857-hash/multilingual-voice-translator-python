import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_rest_api():
    # 1. Languages endpoint
    res = client.get("/api/languages")
    assert res.status_code == 200
    languages = res.json()["languages"]
    assert len(languages) >= 40
    print(f"✓ /api/languages returned {len(languages)} languages.")

    # 2. Translate endpoint
    res = client.post("/api/translate", json={
        "text": "How are you doing today?",
        "source_lang": "en",
        "target_lang": "es"
    })
    assert res.status_code == 200
    translated = res.json()["translated"]
    print(f"✓ /api/translate test: 'How are you doing today?' -> '{translated}'")

    # 3. Rooms endpoint
    res = client.get("/api/rooms/test-room-123")
    assert res.status_code == 200
    assert "participants" in res.json()
    print("✓ /api/rooms/test-room-123 returned valid room state.")

    # 4. Frontend static index
    res = client.get("/")
    assert res.status_code == 200
    assert "VoiceBridge" in res.text
    print("✓ Frontend HTML served successfully at root '/'")

    print("\n[SUCCESS] All FastAPI endpoints verified!")

if __name__ == "__main__":
    test_rest_api()
