# VoiceBridge - Real-Time Multilingual Group Voice Translator

VoiceBridge is a full-stack real-time web application that allows multiple participants (e.g. 5+ members) to communicate across different languages seamlessly. Each member speaks in their native tongue via their microphone, and every recipient automatically receives and hears the audio translated into their own preferred language in real time.

---

## 🌟 Key Features

1. **Multi-Party Room Support**: 5+ participants can join the same room, each with their own chosen language.
2. **Instant Speech-to-Text (STT)**: Speaks into browser microphone in 40+ supported languages.
3. **Concurrent Multi-Target Translation**: Translates incoming speech into each room member's language concurrently with in-memory caching.
4. **Automatic Text-to-Speech (TTS)**: Plays incoming translations in the receiver's native voice automatically.
5. **Interactive Controls**:
   - **Continuous Live Mic** & **Push-to-Talk** modes.
   - **Speech visualizers** & active speaker spotlight.
   - **Transcript feeds** showing both translated and original text subtitles.
   - **Text fallback input** for noisy environments.
   - **Voice customization** (Pitch, Speed, Voice selection).

---

## 🛠️ Architecture

- **Backend**: Python FastAPI + WebSockets + Concurrent Translation Engine.
- **Frontend**: Modern HTML5, Tailwind CSS (Dark/Glassmorphic UI), Web Speech Recognition API, Web Speech Synthesis API, Web Audio API synthesizer.
- **No external API keys required**: Ready to run out of the box.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
python run.py
```
*Or with uvicorn directly:*
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Access the application in your browser at **`http://localhost:8000`**.

---

## 🧪 Testing with 5 Members (Multi-Language Simulation)

Open 5 browser tabs (or test across different devices on your local network `http://<your-local-ip>:8000`):

1. **Tab 1 (Member 1)**: Name: `Alice`, Language: `English 🇺🇸`, Room: `global-sync`
2. **Tab 2 (Member 2)**: Name: `Carlos`, Language: `Spanish 🇪🇸`, Room: `global-sync`
3. **Tab 3 (Member 3)**: Name: `Ravi`, Language: `Hindi 🇮🇳`, Room: `global-sync`
4. **Tab 4 (Member 4)**: Name: `Sophie`, Language: `French 🇫🇷`, Room: `global-sync`
5. **Tab 5 (Member 5)**: Name: `Kenji`, Language: `Japanese 🇯🇵`, Room: `global-sync`

- When **Alice** speaks: *"Hello everyone, welcome to our project discussion."*
- **Carlos** hears & sees: *"Hola a todos, bienvenidos a la discusión de nuestro proyecto."*
- **Ravi** hears & sees: *"सभी को नमस्कार, हमारे प्रोजेक्ट की चर्चा में आपका स्वागत है।"*
- **Sophie** hears & sees: *"Bonjour à tous, bienvenue dans la discussion de notre projet."*
- **Kenji** hears & sees: *"みなさん、こんにちは。プロジェクトの議論へようこそ。"*

---

## 📂 Project Structure

```
multilingual-voice-translator/
├── backend/
│   ├── __init__.py
│   ├── main.py          # FastAPI application & WebSocket hub
│   ├── rooms.py         # Room state and participant manager
│   └── translator.py    # Multi-language translation engine & caching
├── frontend/
│   ├── index.html       # Responsive glassmorphic web UI
│   └── app.js           # STT, TTS, WebSocket & audio controller
├── run.py               # Launcher script
├── requirements.txt     # Python dependencies
├── test_system.py       # Translation engine test
├── test_api.py          # REST API endpoint tests
└── test_websocket.py    # WebSocket multi-client simulation test
```
