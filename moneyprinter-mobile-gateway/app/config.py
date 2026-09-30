import os
from pathlib import Path


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    moneyprinter_base_url = os.getenv(
        "MONEYPRINTER_BASE_URL",
        "http://127.0.0.1:8090",
    ).rstrip("/")
    moneyprinter_api_token = os.getenv("MONEYPRINTER_API_TOKEN", "")
    public_base_url = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_allowed_chat_ids = {
        item.strip()
        for item in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",")
        if item.strip()
    }

    default_language = os.getenv("DEFAULT_LANGUAGE", "ar")
    default_aspect = os.getenv("DEFAULT_ASPECT", "9:16")
    default_video_source = os.getenv("DEFAULT_VIDEO_SOURCE", "pexels")
    default_video_concat_mode = os.getenv("DEFAULT_VIDEO_CONCAT_MODE", "random")
    default_video_clip_duration = int(os.getenv("DEFAULT_VIDEO_CLIP_DURATION", "3"))
    default_voice_name = os.getenv("DEFAULT_VOICE_NAME", "ar-SA-ZariyahNeural")
    default_font_name = os.getenv("DEFAULT_FONT_NAME", "DejaVuSans.ttf")
    default_font_size = int(os.getenv("DEFAULT_FONT_SIZE", "60"))
    default_stroke_width = float(os.getenv("DEFAULT_STROKE_WIDTH", "2"))
    default_subtitle_position = os.getenv("DEFAULT_SUBTITLE_POSITION", "bottom")
    default_bgm_type = os.getenv("DEFAULT_BGM_TYPE", "random")
    default_bgm_volume = float(os.getenv("DEFAULT_BGM_VOLUME", "0.2"))

    poll_seconds = int(os.getenv("POLL_SECONDS", "10"))
    timeout_minutes = int(os.getenv("TIMEOUT_MINUTES", "180"))
    state_path = Path(os.getenv("JOB_STATE_PATH", "/data/jobs.json"))
    max_queue_size = int(os.getenv("MAX_QUEUE_SIZE", "50"))
    dedupe_minutes = int(os.getenv("DEDUPE_MINUTES", "180"))
    telegram_send_video = _as_bool("TELEGRAM_SEND_VIDEO", True)


settings = Settings()
