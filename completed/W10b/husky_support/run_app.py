"""Start the support app: python run_app.py"""
import os

from dotenv import load_dotenv

load_dotenv()

from app.ui import demo  # noqa: E402  (the model needs the keys loaded first)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
