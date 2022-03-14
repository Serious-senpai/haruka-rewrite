import os


HOST = os.environ.get("HOST", "https://haruka39.herokuapp.com/").strip("/")
TOKEN = os.environ["TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]
TOPGG_TOKEN = os.environ.get("TOPGG_TOKEN")
PORT = int(os.environ.get("PORT", 8080))
