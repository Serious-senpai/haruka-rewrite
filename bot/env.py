import os


# Required
DATABASE_URL = os.environ["DATABASE_URL"]
TOKEN = os.environ["TOKEN"]

# Optional
HOST = os.environ.get("HOST", "http://localhost").strip("/")
PORT = int(os.environ.get("PORT", 8080))
TOPGG_TOKEN = os.environ.get("TOPGG_TOKEN", "")
