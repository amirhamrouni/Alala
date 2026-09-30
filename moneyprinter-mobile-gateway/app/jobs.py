import asyncio
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL_STATES = {"ready", "failed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_fingerprint(payload: dict[str, Any]) -> str:
    normalized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class JobStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = asyncio.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}

    async def load(self) -> None:
        async with self._lock:
            if not self.path.exists():
                self._jobs = {}
                return
            try:
                raw = await asyncio.to_thread(self.path.read_text, encoding="utf-8")
                parsed = json.loads(raw)
                self._jobs = parsed if isinstance(parsed, dict) else {}
            except Exception:
                self._jobs = {}

    async def _save_locked(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        body = json.dumps(self._jobs, ensure_ascii=False, indent=2)
        await asyncio.to_thread(tmp.write_text, body, encoding="utf-8")
        await asyncio.to_thread(tmp.replace, self.path)

    async def create(
        self,
        *,
        request: dict[str, Any],
        chat_id: str | None,
        fingerprint: str,
    ) -> dict[str, Any]:
        async with self._lock:
            job_id = uuid.uuid4().hex
            now = utc_now()
            job = {
                "job_id": job_id,
                "fingerprint": fingerprint,
                "state": "queued",
                "request": request,
                "chat_id": chat_id,
                "mpt_task_id": None,
                "videos": [],
                "error": None,
                "created_at": now,
                "updated_at": now,
                "created_unix": time.time(),
            }
            self._jobs[job_id] = job
            await self._save_locked()
            return dict(job)

    async def get(self, job_id: str) -> dict[str, Any] | None:
        async with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    async def update(self, job_id: str, **changes: Any) -> dict[str, Any]:
        async with self._lock:
            job = self._jobs[job_id]
            job.update(changes)
            job["updated_at"] = utc_now()
            await self._save_locked()
            return dict(job)

    async def recent_duplicate(
        self,
        fingerprint: str,
        *,
        within_seconds: int,
    ) -> dict[str, Any] | None:
        cutoff = time.time() - max(0, within_seconds)
        async with self._lock:
            candidates = [
                job
                for job in self._jobs.values()
                if job.get("fingerprint") == fingerprint
                and float(job.get("created_unix", 0) or 0) >= cutoff
                and job.get("state") != "failed"
            ]
            if not candidates:
                return None
            candidates.sort(
                key=lambda item: float(item.get("created_unix", 0) or 0),
                reverse=True,
            )
            return dict(candidates[0])

    async def recoverable(self) -> list[dict[str, Any]]:
        async with self._lock:
            return [
                dict(job)
                for job in self._jobs.values()
                if job.get("state") not in TERMINAL_STATES
            ]
