import os


# Assumed to be true when running in a workflow
BUILD_CHECK = bool(os.environ.get("BUILD_CHECK"))


# Required
DATABASE_URL = os.environ["DATABASE_URL"]
TOKEN = os.environ["TOKEN"]


# Optional
HOST = os.environ.get("HOST", "http://localhost").strip("/")
PORT = int(os.environ.get("PORT", 8080))
TOPGG_TOKEN = os.environ.get("TOPGG_TOKEN")
SECONDARY_TOKEN = os.environ.get("SECONDARY_TOKEN")


# For double-hosting purpose
REDIRECT = bool(os.environ.get("REDIRECT"))
