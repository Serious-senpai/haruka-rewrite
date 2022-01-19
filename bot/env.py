import os
from typing import Optional


def get_host() -> str:
    return os.environ.get("HOST", "https://haruka39.herokuapp.com/").strip("/")


def get_token() -> str:
    return os.environ["TOKEN"]


def get_database_url() -> str:
    return os.environ["DATABASE_URL"]


def get_topgg_token() -> Optional[str]:
    return os.environ.get("TOPGG_TOKEN")
