from app import create_app
import os
import traceback

print("🚀 Starting ClipperAI diagnostic mode...")

app = create_app()

if __name__ == '__main__':
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/uploads", exist_ok=True)
    
    print("✅ App factory created successfully")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print("❌ CRASHED during startup:")
        print(traceback.format_exc())
