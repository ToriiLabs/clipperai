from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    os.makedirs("data", exist_ok=True)  # For ChromaDB
    app.run(debug=True)
