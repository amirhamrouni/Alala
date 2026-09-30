import asyncio
from typing import Any

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import settings
from .moneyprinter import create_video_job, get_task, wait_for_video


app = FastAPI(title="MoneyPrinter Mobile Gateway", version="1.0.0")


class VideoRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    video_language: str | None = None
    video_aspect: str | None = None
    video_count: int = 1
    subtitle_enabled: bool = True


async def send_telegram_message(chat_id: str, text: str) -> None:
    if not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(url, json={"chat_id": chat_id, "text": text, "disable_web_page_preview": False})


async def notify_when_done(task_id: str, chat_id: str | None = None) -> None:
    result = await wait_for_video(task_id)
    if not chat_id:
        return
    if result["status"] == "completed":
        links = "\n".join(result["videos"])
        await send_telegram_message(chat_id, f"Video ready:\n{links}")
    else:
        await send_telegram_message(chat_id, f"Video job {task_id} ended with status: {result['status']}")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/make-video")
async def make_video(body: VideoRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    try:
        job = await create_video_job(
            body.topic,
            video_language=body.video_language,
            video_aspect=body.video_aspect,
            video_count=body.video_count,
            subtitle_enabled=body.subtitle_enabled,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"MoneyPrinterTurbo API error: {exc}") from exc
    background_tasks.add_task(notify_when_done, job["task_id"])
    return {"task_id": job["task_id"], "status_url": f"/tasks/{job['task_id']}"}


@app.get("/tasks/{task_id}")
async def task_status(task_id: str) -> dict[str, Any]:
    try:
        return await get_task(task_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"MoneyPrinterTurbo API error: {exc}") from exc


@app.post("/telegram/webhook")
async def telegram_webhook(update: dict[str, Any], background_tasks: BackgroundTasks) -> dict[str, bool]:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    text = (message.get("text") or "").strip()

    if not chat_id or not text:
        return {"ok": True}
    if settings.telegram_allowed_chat_ids and chat_id not in settings.telegram_allowed_chat_ids:
        await send_telegram_message(chat_id, "This bot is private.")
        return {"ok": True}

    lowered = text.lower()
    for prefix in ("/video", "اعملي فيديو", "اعمل فيديو", "video"):
        if lowered.startswith(prefix.lower()):
            topic = text[len(prefix) :].strip(" :-")
            break
    else:
        topic = text

    if len(topic) < 3:
        await send_telegram_message(chat_id, "Send a topic, for example: اعملي فيديو عن الذكاء الاصطناعي")
        return {"ok": True}

    job = await create_video_job(topic)
    await send_telegram_message(chat_id, f"Started video job: {job['task_id']}")
    background_tasks.add_task(notify_when_done, job["task_id"], chat_id)
    return {"ok": True}


@app.on_event("startup")
async def startup_notice() -> None:
    await asyncio.sleep(0)
