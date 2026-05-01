from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    print("✅ ClipperAI starting...")
    print("📍 Server running at: http://0.0.0.0:5000")
    print("⏳ First run may take a few minutes to load the model...")

    # No debug, no reloader — this fixes the restart crash in Codespaces
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
