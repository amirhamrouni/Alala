import asyncio
from typing import Any

import httpx

from .config import settings


def _headers() -> dict[str, str]:
    if not settings.moneyprinter_api_token:
        return {}
    return {"Authorization": f"Bearer {settings.moneyprinter_api_token}"}


def _normalize_task_id(response_json: dict[str, Any]) -> str:
    data = response_json.get("data", response_json)
    task_id = data.get("task_id") or data.get("id")
    if not task_id:
        raise RuntimeError(
            f"MoneyPrinterTurbo did not return a task_id: {response_json}"
        )
    return str(task_id)


def _extract_video_urls(task_json: dict[str, Any]) -> list[str]:
    data = task_json.get("data", task_json)
    urls: list[str] = []
    for key in ("combined_videos", "videos"):
        values = data.get(key) or []
        if isinstance(values, (str, dict)):
            values = [values]
        for value in values:
            if isinstance(value, dict):
                value = value.get("url") or value.get("path") or value.get("file")
            if value:
                urls.append(str(value))
    return list(dict.fromkeys(urls))


def _normalized_task_state(task_json: dict[str, Any]) -> str:
    data = task_json.get("data", task_json)
    raw = data.get("state")
    progress = int(data.get("progress", 0) or 0)

    if raw in (1, "1"):
        return "completed"
    if raw in (-1, "-1"):
        return "failed"

    state = str(raw or "").strip().lower()
    if state in {"complete", "completed", "success", "succeeded", "finished"}:
        return "completed"
    if state in {"failed", "error", "cancelled", "canceled"}:
        return "failed"
    if progress >= 100 and _extract_video_urls(task_json):
        return "completed"
    return "running"


def _error_text(task_json: dict[str, Any]) -> str:
    data = task_json.get("data", task_json)
    return str(
        data.get("error")
        or data.get("message")
        or task_json.get("message")
        or "MoneyPrinterTurbo task failed"
    )


async def create_video_job(topic: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        "video_subject": topic,
        "video_language": overrides.get("video_language") or settings.default_language,
        "video_aspect": overrides.get("video_aspect") or settings.default_aspect,
        "video_source": overrides.get("video_source") or settings.default_video_source,
        "video_concat_mode": (
            overrides.get("video_concat_mode") or settings.default_video_concat_mode
        ),
        "video_clip_duration": int(
            overrides.get("video_clip_duration")
            or settings.default_video_clip_duration
        ),
        "video_count": int(overrides.get("video_count", 1)),
        "voice_name": overrides.get("voice_name") or settings.default_voice_name,
        "bgm_type": overrides.get("bgm_type") or settings.default_bgm_type,
        "bgm_volume": float(
            overrides.get("bgm_volume")
            if overrides.get("bgm_volume") is not None
            else settings.default_bgm_volume
        ),
        "subtitle_enabled": bool(overrides.get("subtitle_enabled", True)),
        "subtitle_position": (
            overrides.get("subtitle_position") or settings.default_subtitle_position
        ),
        "subtitle_display_mode": overrides.get("subtitle_display_mode") or "sentence",
        "font_name": overrides.get("font_name") or settings.default_font_name,
        "font_size": int(overrides.get("font_size") or settings.default_font_size),
        "stroke_width": float(
            overrides.get("stroke_width")
            if overrides.get("stroke_width") is not None
            else settings.default_stroke_width
        ),
        "text_fore_color": overrides.get("text_fore_color") or "#FFFFFF",
        "stroke_color": overrides.get("stroke_color") or "#000000",
    }

    passthrough = {
        key: value
        for key, value in overrides.items()
        if value is not None and key not in payload
    }
    payload.update(passthrough)

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.moneyprinter_base_url}/api/v1/videos",
            json=payload,
            headers=_headers(),
        )
        response.raise_for_status()
        body = response.json()
        return {"task_id": _normalize_task_id(body), "raw": body, "payload": payload}


async def get_task(task_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(
            f"{settings.moneyprinter_base_url}/api/v1/tasks/{task_id}",
            headers=_headers(),
        )
        response.raise_for_status()
        return response.json()


async def wait_for_video(task_id: str) -> dict[str, Any]:
    deadline = asyncio.get_running_loop().time() + settings.timeout_minutes * 60
    last_task: dict[str, Any] = {}

    while asyncio.get_running_loop().time() < deadline:
        last_task = await get_task(task_id)
        state = _normalized_task_state(last_task)
        urls = _extract_video_urls(last_task)

        if state == "completed":
            return {
                "task_id": task_id,
                "status": "completed",
                "videos": urls,
                "raw": last_task,
            }
        if state == "failed":
            return {
                "task_id": task_id,
                "status": "failed",
                "videos": urls,
                "error": _error_text(last_task),
                "raw": last_task,
            }

        await asyncio.sleep(settings.poll_seconds)

    return {
        "task_id": task_id,
        "status": "timeout",
        "videos": _extract_video_urls(last_task),
        "raw": last_task,
    }
