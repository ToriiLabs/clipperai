from app import create_app
import os
import subprocess
import time
import sys

app = create_app()

def start_ollama():
    """Start Ollama server automatically if it's not running"""
    print("🔄 Checking Ollama server...")
    
    try:
        # Test if Ollama is already running
        import requests
        requests.get("http://localhost:11434/api/version", timeout=2)
        print("✅ Ollama is already running")
        return
    except:
        print("🚀 Starting Ollama server in background...")
        try:
            # Start ollama serve in background
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(4)  # Give it time to start
            print("✅ Ollama server started successfully")
        except FileNotFoundError:
            print("❌ Ollama not found! Make sure it's installed.")
            print("   Run: curl -fsSL https://ollama.com/install.sh | sh")
            sys.exit(1)

if __name__ == '__main__':
    start_ollama()   # ← Add this line
    
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    print("✅ ClipperAI starting on http://0.0.0.0:5000")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
