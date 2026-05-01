from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    print("✅ ClipperAI starting...")
    print("📍 Trying to run on http://0.0.0.0:5000")
    
    # Maximum stability settings
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
