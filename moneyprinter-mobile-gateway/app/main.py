import asyncio
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import settings
from .jobs import JobStore, request_fingerprint
from .moneyprinter import create_video_job, get_task, wait_for_video


app = FastAPI(title="MoneyPrinter Mobile Gateway", version="2.0.0")
store = JobStore(settings.state_path)
queue: asyncio.Queue[str] = asyncio.Queue(maxsize=settings.max_queue_size)
worker_task: asyncio.Task | None = None


class VideoRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    video_language: str | None = None
    video_aspect: str | None = None
    video_count: int = 1
    subtitle_enabled: bool = True
    voice_name: str | None = None
    font_name: str | None = None
    font_size: int | None = None


def _job_request(body: VideoRequest) -> dict[str, Any]:
    return {
        key: value
        for key, value in body.model_dump().items()
        if value is not None
    }


async def send_telegram_message(chat_id: str, text: str) -> None:
    if not settings.telegram_bot_token:
        return
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": False,
            },
        )
        response.raise_for_status()


async def send_telegram_result(chat_id: str, job: dict[str, Any]) -> None:
    videos = job.get("videos") or []
    if not videos:
        await send_telegram_message(
            chat_id,
            f"اكتملت المهمة {job['job_id']} لكن لم يرجع مسار فيديو.",
        )
        return

    first = str(videos[0])
    if settings.telegram_send_video and first.startswith(("http://", "https://")):
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendVideo"
        async with httpx.AsyncClient(timeout=180) as client:
            response = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "video": first,
                    "caption": f"تم إنشاء الفيديو\njob_id: {job['job_id']}",
                },
            )
        if response.is_success:
            return

    links = "\n".join(str(item) for item in videos)
    await send_telegram_message(
        chat_id,
        f"تم إنشاء الفيديو\njob_id: {job['job_id']}\n{links}",
    )


async def process_job(job_id: str) -> None:
    job = await store.get(job_id)
    if not job:
        return

    try:
        task_id = job.get("mpt_task_id")
        if not task_id:
            await store.update(job_id, state="submitting", error=None)
            request = dict(job["request"])
            topic = request.pop("topic")
            submitted = await create_video_job(topic, **request)
            task_id = submitted["task_id"]
            await store.update(
                job_id,
                state="rendering",
                mpt_task_id=task_id,
            )
        else:
            await store.update(job_id, state="rendering")

        result = await wait_for_video(str(task_id))
        if result["status"] == "completed":
            final = await store.update(
                job_id,
                state="ready",
                videos=result.get("videos", []),
                error=None,
            )
            if final.get("chat_id"):
                await send_telegram_result(str(final["chat_id"]), final)
            return

        error = result.get("error") or result["status"]
        final = await store.update(job_id, state="failed", error=str(error))
        if final.get("chat_id"):
            await send_telegram_message(
                str(final["chat_id"]),
                f"فشل إنشاء الفيديو\njob_id: {job_id}\n{error}",
            )
    except Exception as exc:
        final = await store.update(job_id, state="failed", error=str(exc)[:1000])
        if final.get("chat_id"):
            try:
                await send_telegram_message(
                    str(final["chat_id"]),
                    f"فشل إنشاء الفيديو\njob_id: {job_id}\n{str(exc)[:500]}",
                )
            except Exception:
                pass


async def worker() -> None:
    while True:
        job_id = await queue.get()
        try:
            await process_job(job_id)
        finally:
            queue.task_done()


async def enqueue(
    request: dict[str, Any],
    *,
    chat_id: str | None = None,
) -> tuple[dict[str, Any], bool]:
    fp = request_fingerprint(request)
    duplicate = await store.recent_duplicate(
        fp,
        within_seconds=settings.dedupe_minutes * 60,
    )
    if duplicate:
        return duplicate, True

    if queue.full():
        raise HTTPException(status_code=503, detail="Video queue is full")

    job = await store.create(
        request=request,
        chat_id=chat_id,
        fingerprint=fp,
    )
    queue.put_nowait(job["job_id"])
    return job, False


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "queue_size": queue.qsize(),
        "queue_limit": settings.max_queue_size,
    }


@app.post("/make-video")
async def make_video(body: VideoRequest) -> dict[str, Any]:
    request = _job_request(body)
    job, duplicate = await enqueue(request)
    return {
        "job_id": job["job_id"],
        "state": job["state"],
        "duplicate": duplicate,
        "status_url": f"/jobs/{job['job_id']}",
    }


@app.get("/jobs/{job_id}")
async def job_status(job_id: str) -> dict[str, Any]:
    job = await store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return job


@app.get("/tasks/{task_id}")
async def task_status(task_id: str) -> dict[str, Any]:
    try:
        return await get_task(task_id)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=exc.response.text,
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"MoneyPrinterTurbo API error: {exc}",
        ) from exc


@app.post("/telegram/webhook")
async def telegram_webhook(update: dict[str, Any]) -> dict[str, Any]:
    message = update.get("message") or update.get("edited_message") or {}
    chat = message.get("chat") or {}
    chat_id = str(chat.get("id", ""))
    text = (message.get("text") or "").strip()

    if not chat_id or not text:
        return {"ok": True}

    if settings.telegram_allowed_chat_ids and chat_id not in settings.telegram_allowed_chat_ids:
        await send_telegram_message(chat_id, "هذا البوت خاص.")
        return {"ok": True}

    lowered = text.lower()
    for prefix in (
        "/video",
        "اعملي فيديو",
        "اعمل فيديو",
        "اصنع فيديو",
        "أنشئ فيديو",
        "video",
    ):
        if lowered.startswith(prefix.lower()):
            topic = text[len(prefix):].strip(" :-")
            break
    else:
        topic = text

    if topic.startswith("عن "):
        topic = topic[3:].strip()

    if len(topic) < 3:
        await send_telegram_message(
            chat_id,
            "أرسل موضوع الفيديو، مثال: اعمل فيديو عن فوائد الذكاء الاصطناعي",
        )
        return {"ok": True}

    request = {
        "topic": topic,
        "video_language": settings.default_language,
        "video_aspect": settings.default_aspect,
        "video_count": 1,
        "subtitle_enabled": True,
    }
    job, duplicate = await enqueue(request, chat_id=chat_id)

    if duplicate:
        await send_telegram_message(
            chat_id,
            f"نفس الطلب موجود بالفعل.\njob_id: {job['job_id']}\nالحالة: {job['state']}",
        )
    else:
        await send_telegram_message(
            chat_id,
            f"بدأت إنشاء الفيديو عن: {topic}\njob_id: {job['job_id']}",
        )
    return {"ok": True, "job_id": job["job_id"], "duplicate": duplicate}


@app.on_event("startup")
async def startup() -> None:
    global worker_task
    await store.load()
    worker_task = asyncio.create_task(worker())

    for job in await store.recoverable():
        if queue.full():
            break
        queue.put_nowait(job["job_id"])


@app.on_event("shutdown")
async def shutdown() -> None:
    global worker_task
    if worker_task is not None:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        worker_task = None
