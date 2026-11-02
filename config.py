import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip().lstrip("@")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/postbot.db")

raw_admins = os.getenv("ADMIN_IDS", "").strip()
ADMIN_IDS = set()
for item in raw_admins.replace(",", " ").split():
    if item.isdigit():
        ADMIN_IDS.add(int(item))

DONATE_LINK = os.getenv("DONATE_LINK", "").strip()
DONATE_TEXT = os.getenv("DONATE_TEXT", "Support PostBot Development\n\nIf you find this bot helpful, you can support our development to keep servers running 24/7 with high speed!").strip()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

ASSETS_DIR = BASE_DIR / "assets"

data_dir = BASE_DIR / Path(DATABASE_PATH).parent
data_dir.mkdir(parents=True, exist_ok=True)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
