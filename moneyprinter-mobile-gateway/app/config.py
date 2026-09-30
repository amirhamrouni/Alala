import os
from pathlib import Path


class Settings:
    moneyprinter_base_url = os.getenv(
        "MONEYPRINTER_BASE_URL",
        "https://rule-unnamed-could.ngrok-free.dev",
    ).rstrip("/")
    moneyprinter_api_token = os.getenv("MONEYPRINTER_API_TOKEN", "")
    public_base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_allowed_chat_ids = {
        item.strip()
        for item in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",")
        if item.strip()
    }
    default_language = os.getenv("DEFAULT_LANGUAGE", "Arabic")
    default_aspect = os.getenv("DEFAULT_ASPECT", "9:16")
    poll_seconds = int(os.getenv("POLL_SECONDS", "15"))
    timeout_minutes = int(os.getenv("TIMEOUT_MINUTES", "180"))
    state_path = Path(os.getenv("JOB_STATE_PATH", "/data/jobs.json"))
    max_queue_size = int(os.getenv("MAX_QUEUE_SIZE", "50"))


settings = Settings()
import os


class Settings:
    moneyprinter_base_url = os.getenv(
        "MONEYPRINTER_BASE_URL",
        "https://rule-unnamed-could.ngrok-free.dev",
    ).rstrip("/")
    moneyprinter_api_token = os.getenv("MONEYPRINTER_API_TOKEN", "")
    public_base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_allowed_chat_ids = {
        item.strip()
        for item in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",")
        if item.strip()
    }
    default_language = os.getenv("DEFAULT_LANGUAGE", "Arabic")
    default_aspect = os.getenv("DEFAULT_ASPECT", "9:16")
    poll_seconds = int(os.getenv("POLL_SECONDS", "15"))
    timeout_minutes = int(os.getenv("TIMEOUT_MINUTES", "180"))


settings = Settings()
