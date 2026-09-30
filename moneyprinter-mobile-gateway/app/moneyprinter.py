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
        raise RuntimeError(f"MoneyPrinterTurbo did not return a task_id: {response_json}")
    return str(task_id)


def _extract_video_urls(task_json: dict[str, Any]) -> list[str]:
    data = task_json.get("data", task_json)
    urls: list[str] = []
    for key in ("combined_videos", "videos"):
        values = data.get(key) or []
        if isinstance(values, str):
            values = [values]
        urls.extend(str(value) for value in values if value)
    return urls


async def create_video_job(topic: str, **overrides: Any) -> dict[str, Any]:
    payload = {
        "video_subject": topic,
        "video_language": overrides.get("video_language", settings.default_language),
        "video_aspect": overrides.get("video_aspect", settings.default_aspect),
        "video_count": int(overrides.get("video_count", 1)),
        "subtitle_enabled": bool(overrides.get("subtitle_enabled", True)),
        "bgm_type": overrides.get("bgm_type", "random"),
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.moneyprinter_base_url}/api/v1/videos",
            json=payload,
            headers=_headers(),
        )
        response.raise_for_status()
        body = response.json()
        return {"task_id": _normalize_task_id(body), "raw": body}


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
        data = last_task.get("data", last_task)
        state = str(data.get("state", "")).lower()
        progress = int(data.get("progress", 0) or 0)
        urls = _extract_video_urls(last_task)

        if urls and (progress >= 100 or state in {"complete", "completed", "success", "finished"}):
            return {"task_id": task_id, "status": "completed", "videos": urls, "raw": last_task}
        if state in {"failed", "error"}:
            return {"task_id": task_id, "status": "failed", "videos": urls, "raw": last_task}

        await asyncio.sleep(settings.poll_seconds)

    return {"task_id": task_id, "status": "timeout", "videos": _extract_video_urls(last_task), "raw": last_task}
