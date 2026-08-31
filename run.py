import uvicorn
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n[VoiceBridge] Opening application in default browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    print("=" * 65)
    print("  🚀 Starting VoiceBridge - Real-Time Multilingual Translator")
    print("  🌐 Access the Web UI at: http://127.0.0.1:8000")
    print("=" * 65)
    
    # Launch browser automatically in a background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
