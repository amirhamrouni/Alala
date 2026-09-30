#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def secret(name: str) -> str:
    value = os.getenv(name, "").strip()
    if value:
        return value
    try:
        from google.colab import userdata
        value = userdata.get(name)
        return value.strip() if value else ""
    except Exception:
        return ""


def healthy(url: str) -> bool:
    try:
        import requests
        return requests.get(url, timeout=3).status_code == 200
    except Exception:
        return False


def task_id_from(obj):
    if isinstance(obj, dict):
        for key in ("task_id", "taskId", "id"):
            if key in obj and isinstance(obj[key], (str, int)):
                return str(obj[key])
        for value in obj.values():
            found = task_id_from(value)
            if found:
                return found
    return None


def state_from(obj):
    data = obj.get("data", obj) if isinstance(obj, dict) else {}
    return data.get("state"), data


def set_scalar(text: str, key: str, value_literal: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}\s*=\s*.*$"
    replacement = f"{key} = {value_literal}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    return text.rstrip() + "\n" + replacement + "\n"


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-q", "uv", "pyngrok", "requests"],
        check=True,
    )

    import requests
    from pyngrok import ngrok

    repo = Path("/content/MoneyPrinterTurbo")
    upstream = "https://github.com/harry0703/MoneyPrinterTurbo.git"
    api = "http://127.0.0.1:8090"

    if not (repo / ".git").is_dir():
        if repo.exists():
            subprocess.run(["rm", "-rf", str(repo)], check=True)
        subprocess.run(["git", "clone", "--depth", "1", upstream, str(repo)], check=True)
    else:
        subprocess.run(["git", "-C", str(repo), "pull", "--ff-only"], check=True)

    subprocess.run(["uv", "python", "install", "3.11"], check=True)
    subprocess.run(["uv", "sync", "--frozen", "--python", "3.11"], cwd=repo, check=True)

    cfg = repo / "config.toml"
    if not cfg.exists():
        cfg.write_text(
            (repo / "config.example.toml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    raw = cfg.read_text(encoding="utf-8")
    raw = set_scalar(raw, "listen_port", "8090")

    pexels_key = secret("PEXELS_API_KEY") or secret("MPT_PEXELS_API_KEY")
    if pexels_key:
        raw = set_scalar(raw, "pexels_api_keys", json.dumps([pexels_key]))

    gemini_key = secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY")
    if gemini_key:
        raw = set_scalar(raw, "llm_provider", '"gemini"')
        raw = set_scalar(raw, "gemini_api_key", json.dumps(gemini_key))
        gemini_model = secret("GEMINI_MODEL")
        if gemini_model:
            raw = set_scalar(raw, "gemini_model_name", json.dumps(gemini_model))

    cfg.write_text(raw, encoding="utf-8")

    if not healthy("http://127.0.0.1:8501/_stcore/health"):
        web_log = open("/content/mpt-webui.log", "a", encoding="utf-8")
        subprocess.Popen(
            [
                "uv", "run", "streamlit", "run", "webui/Main.py",
                "--server.port=8501", "--server.address=0.0.0.0",
                "--browser.gatherUsageStats=False",
            ],
            cwd=repo,
            stdout=web_log,
            stderr=subprocess.STDOUT,
        )
        for _ in range(60):
            if healthy("http://127.0.0.1:8501/_stcore/health"):
                break
            time.sleep(2)

    if not healthy(api + "/ping"):
        api_log = open("/content/mpt-api.log", "a", encoding="utf-8")
        subprocess.Popen(
            ["uv", "run", "python", "main.py"],
            cwd=repo,
            stdout=api_log,
            stderr=subprocess.STDOUT,
        )
        for _ in range(60):
            if healthy(api + "/ping"):
                break
            time.sleep(2)

    if not healthy(api + "/ping"):
        raise RuntimeError("MoneyPrinter API did not start on port 8090")

    ngrok_token = secret("NGROK_AUTHTOKEN")
    if ngrok_token:
        ngrok.set_auth_token(ngrok_token)
        try:
            ngrok.kill()
        except Exception:
            pass
        tunnel = ngrok.connect(addr="http://127.0.0.1:8501", proto="http", bind_tls=True)
        print("WebUI:", tunnel.public_url, flush=True)

    tg_token = secret("TELEGRAM_BOT_TOKEN")
    if not tg_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing from Colab Secrets")

    tg = f"https://api.telegram.org/bot{tg_token}"
    session = requests.Session()

    session.post(
        tg + "/deleteWebhook",
        json={"drop_pending_updates": False},
        timeout=20,
    ).raise_for_status()

    me = session.get(tg + "/getMe", timeout=20).json()
    if not me.get("ok"):
        raise RuntimeError("Telegram token rejected")

    print("Telegram bot ready: @" + me["result"]["username"], flush=True)
    print("SUBTITLES=OFF", flush=True)
    print("READY", flush=True)

    def send(chat, text):
        return session.post(
            tg + "/sendMessage",
            json={"chat_id": chat, "text": text},
            timeout=30,
        )

    def make_video(chat, topic):
        send(chat, "بدأت إنشاء الفيديو عن: " + topic + "\nسأرسله هنا عند اكتماله.")
        payload = {
            "video_subject": topic,
            "video_language": "ar",
            "paragraph_number": 1,
            "video_source": "pexels",
            "video_aspect": "9:16",
            "video_concat_mode": "random",
            "video_clip_duration": 3,
            "video_count": 1,
            "voice_name": "ar-SA-ZariyahNeural",
            "voice_volume": 1.0,
            "voice_rate": 1.0,
            "bgm_type": "random",
            "bgm_volume": 0.2,
            "subtitle_enabled": False,
        }

        response = session.post(api + "/api/v1/videos", json=payload, timeout=60)
        response.raise_for_status()
        tid = task_id_from(response.json())
        if not tid:
            raise RuntimeError("No task id: " + response.text[:300])

        for _ in range(180):
            info = session.get(api + "/api/v1/tasks/" + tid, timeout=30).json()
            state, data = state_from(info)
            if state == 1:
                break
            if state == -1:
                raise RuntimeError(
                    str(data.get("error") or data.get("message") or info)[:500]
                )
            time.sleep(10)
        else:
            raise RuntimeError("Video generation timed out")

        files = sorted((repo / "storage" / "tasks" / tid).glob("final-*.mp4"))
        if not files:
            files = sorted((repo / "storage" / "tasks" / tid).glob("*.mp4"))
        if not files:
            raise RuntimeError("Completed but video file was not found")

        with files[-1].open("rb") as file_handle:
            resp = session.post(
                tg + "/sendVideo",
                data={"chat_id": chat, "caption": "تم إنشاء الفيديو"},
                files={"video": (files[-1].name, file_handle, "video/mp4")},
                timeout=180,
            )

        if not resp.json().get("ok"):
            with files[-1].open("rb") as file_handle:
                session.post(
                    tg + "/sendDocument",
                    data={"chat_id": chat, "caption": "تم إنشاء الفيديو"},
                    files={"document": (files[-1].name, file_handle, "video/mp4")},
                    timeout=180,
                ).raise_for_status()

    offset = 0
    print("Send /start to the bot.", flush=True)

    while True:
        try:
            updates = session.get(
                tg + "/getUpdates",
                params={"offset": offset, "timeout": 25},
                timeout=35,
            ).json()

            for update in updates.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message") or {}
                chat = (msg.get("chat") or {}).get("id")
                text = (msg.get("text") or "").strip()
                if not chat or not text:
                    continue

                if text.startswith("/start"):
                    send(chat, "أرسل موضوع الفيديو فقط، مثال: فوائد الذكاء الاصطناعي في الدراسة")
                else:
                    topic = re.sub(
                        r"^(اعملي|اعمل|اصنع|أنشئ)\s+(لي\s+)?فيديو\s+(عن\s+)?",
                        "",
                        text,
                    ).strip() or text
                    try:
                        make_video(chat, topic)
                    except Exception as exc:
                        send(chat, "تعذر إنشاء الفيديو: " + str(exc)[:700])
        except Exception as exc:
            print("poll error:", type(exc).__name__, str(exc)[:200], flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
