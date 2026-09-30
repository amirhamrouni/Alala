#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def sh(cmd, *, cwd=None, check=True):
    print("$", " ".join(map(str, cmd)), flush=True)
    return subprocess.run(cmd, cwd=cwd, check=check)


def pip_install(*packages: str) -> None:
    sh([sys.executable, "-m", "pip", "install", "-q", *packages])


def http_ok(url: str, timeout: int = 3) -> bool:
    try:
        import requests

        return requests.get(url, timeout=timeout).status_code == 200
    except Exception:
        return False


def wait_http(url: str, seconds: int, *, log_path: Path | None = None) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if http_ok(url):
            return
        time.sleep(2)
    if log_path and log_path.exists():
        print(log_path.read_text(encoding="utf-8", errors="replace")[-4000:], flush=True)
    raise RuntimeError(f"service did not become healthy: {url}")


def set_scalar(text: str, key: str, value_literal: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}\s*=\s*.*$"
    replacement = f"{key} = {value_literal}"
    if re.search(pattern, text):
        return re.sub(pattern, replacement, text, count=1)
    return text.rstrip() + "\n" + replacement + "\n"


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


def normalize_task_id(obj):
    if isinstance(obj, dict):
        for key in ("task_id", "taskId", "id"):
            value = obj.get(key)
            if isinstance(value, (str, int)) and str(value):
                return str(value)
        for value in obj.values():
            found = normalize_task_id(value)
            if found:
                return found
    return None


def task_state(obj):
    data = obj.get("data", obj) if isinstance(obj, dict) else {}
    return data.get("state"), data


def completed_state(state) -> bool:
    return state == 1 or str(state).lower() in {
        "1",
        "success",
        "completed",
        "complete",
        "finished",
        "ready",
    }


def failed_state(state) -> bool:
    return state == -1 or str(state).lower() in {"-1", "failed", "error"}


def main() -> None:
    pip_install("uv", "pyngrok", "requests")
    import requests

    mpt = Path("/content/MoneyPrinterTurbo")
    upstream = "https://github.com/harry0703/MoneyPrinterTurbo.git"
    alala = Path("/content/Alala")
    patch_script = alala / "moneyprinter-mobile-gateway/scripts/patch_moneyprinter_arabic.py"

    if (mpt / ".git").is_dir():
        sh(["git", "-C", str(mpt), "pull", "--ff-only"])
    else:
        if mpt.exists():
            sh(["rm", "-rf", str(mpt)])
        sh(["git", "clone", "--depth", "1", upstream, str(mpt)])

    sh(["uv", "python", "install", "3.11"])
    sh(["uv", "sync", "--frozen", "--python", "3.11"], cwd=mpt)
    sh(["apt-get", "update", "-qq"])
    sh(["apt-get", "install", "-y", "-qq", "fonts-dejavu"])

    if not patch_script.is_file():
        raise RuntimeError(f"Arabic patch script missing: {patch_script}")
    sh([sys.executable, str(patch_script), "--repo", str(mpt)])

    api_port = 8090
    web_port = 8501
    cfg = mpt / "config.toml"
    if not cfg.exists():
        cfg.write_text((mpt / "config.example.toml").read_text(encoding="utf-8"), encoding="utf-8")
    raw = cfg.read_text(encoding="utf-8")
    raw = set_scalar(raw, "listen_port", str(api_port))
    raw = set_scalar(raw, "video_source", '"pexels"')

    pexels = secret("PEXELS_API_KEY") or secret("MPT_PEXELS_API_KEY")
    if pexels:
        raw = set_scalar(raw, "pexels_api_keys", json.dumps([pexels]))

    openrouter = secret("OPENROUTER_API_KEY")
    gemini = secret("GEMINI_API_KEY") or secret("GOOGLE_API_KEY")
    if openrouter:
        raw = set_scalar(raw, "llm_provider", '"openrouter"')
        raw = set_scalar(raw, "openrouter_api_key", json.dumps(openrouter))
        model = secret("OPENROUTER_MODEL") or "minimax/minimax-m3:free"
        raw = set_scalar(raw, "openrouter_model_name", json.dumps(model))
    elif gemini:
        raw = set_scalar(raw, "llm_provider", '"gemini"')
        raw = set_scalar(raw, "gemini_api_key", json.dumps(gemini))
        model = secret("GEMINI_MODEL")
        if model:
            raw = set_scalar(raw, "gemini_model_name", json.dumps(model))

    cfg.write_text(raw, encoding="utf-8")

    for port in (api_port, web_port):
        subprocess.run(
            ["bash", "-lc", f"fuser -k {port}/tcp >/dev/null 2>&1 || true"],
            check=False,
        )
    time.sleep(1)

    api_log_path = Path("/content/mpt-api.log")
    web_log_path = Path("/content/mpt-webui.log")
    api_log = api_log_path.open("w", encoding="utf-8")
    web_log = web_log_path.open("w", encoding="utf-8")
    subprocess.Popen(
        ["uv", "run", "python", "main.py"],
        cwd=mpt,
        stdout=api_log,
        stderr=subprocess.STDOUT,
    )
    subprocess.Popen(
        [
            "uv",
            "run",
            "streamlit",
            "run",
            "webui/Main.py",
            f"--server.port={web_port}",
            "--server.address=0.0.0.0",
            "--browser.gatherUsageStats=False",
            "--client.toolbarMode=minimal",
            "--server.showEmailPrompt=False",
        ],
        cwd=mpt,
        stdout=web_log,
        stderr=subprocess.STDOUT,
    )

    api = f"http://127.0.0.1:{api_port}"
    wait_http(api + "/ping", 120, log_path=api_log_path)
    wait_http(
        f"http://127.0.0.1:{web_port}/_stcore/health",
        120,
        log_path=web_log_path,
    )

    ngrok_token = secret("NGROK_AUTHTOKEN")
    if ngrok_token:
        from pyngrok import ngrok

        ngrok.set_auth_token(ngrok_token)
        try:
            ngrok.kill()
        except Exception:
            pass
        tunnel = ngrok.connect(
            addr=f"http://127.0.0.1:{web_port}",
            proto="http",
            bind_tls=True,
        )
        print("WEBUI=", tunnel.public_url, flush=True)
    else:
        print("WEBUI=LOCAL_ONLY", flush=True)

    tg_token = secret("TELEGRAM_BOT_TOKEN")
    print("MPT_API=PASS", flush=True)
    print("WEBUI=PASS", flush=True)
    print("ARABIC_RTL=PASS", flush=True)

    if not tg_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing from Colab Secrets")

    tg = f"https://api.telegram.org/bot{tg_token}"
    session = requests.Session()

    webhook_resp = session.post(
        tg + "/deleteWebhook",
        json={"drop_pending_updates": False},
        timeout=30,
    )
    webhook_resp.raise_for_status()

    me_resp = session.get(tg + "/getMe", timeout=30)
    me_resp.raise_for_status()
    me = me_resp.json()
    if not me.get("ok"):
        raise RuntimeError("Telegram token rejected")
    username = me["result"]["username"]
    print(f"TELEGRAM=PASS @{username}", flush=True)
    print("READY", flush=True)

    def send(chat, text):
        r = session.post(
            tg + "/sendMessage",
            json={"chat_id": chat, "text": text},
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()
        if not body.get("ok"):
            raise RuntimeError(f"Telegram sendMessage failed: {body}")
        return r

    def send_video(chat, path: Path):
        with path.open("rb") as fh:
            r = session.post(
                tg + "/sendVideo",
                data={"chat_id": chat, "caption": "تم إنشاء الفيديو"},
                files={"video": (path.name, fh, "video/mp4")},
                timeout=240,
            )
        body = r.json()
        if body.get("ok"):
            return
        with path.open("rb") as fh:
            r = session.post(
                tg + "/sendDocument",
                data={"chat_id": chat, "caption": "تم إنشاء الفيديو"},
                files={"document": (path.name, fh, "video/mp4")},
                timeout=240,
            )
            r.raise_for_status()
            body = r.json()
            if not body.get("ok"):
                raise RuntimeError(f"Telegram sendDocument failed: {body}")

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
            "subtitle_enabled": True,
            "font_name": "DejaVuSans.ttf",
        }
        response = session.post(api + "/api/v1/videos", json=payload, timeout=90)
        response.raise_for_status()
        tid = normalize_task_id(response.json())
        if not tid:
            raise RuntimeError("MoneyPrinter did not return task_id")

        deadline = time.time() + 45 * 60
        while time.time() < deadline:
            info_resp = session.get(api + "/api/v1/tasks/" + tid, timeout=30)
            info_resp.raise_for_status()
            info = info_resp.json()
            state, data = task_state(info)
            if completed_state(state):
                break
            if failed_state(state):
                raise RuntimeError(
                    str(data.get("error") or data.get("message") or info)[:700]
                )
            time.sleep(10)
        else:
            raise RuntimeError("Video generation timed out")

        task_dir = mpt / "storage" / "tasks" / tid
        files = sorted(task_dir.glob("final-*.mp4"), key=lambda p: p.stat().st_mtime)
        if not files:
            files = sorted(task_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if not files:
            raise RuntimeError(f"completed but MP4 not found for task {tid}")
        send_video(chat, files[-1])

    offset = 0
    while True:
        try:
            poll = session.get(
                tg + "/getUpdates",
                params={
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": json.dumps(["message"]),
                },
                timeout=35,
            )
            if poll.status_code == 409:
                try:
                    body = poll.json()
                    description = body.get("description", "another getUpdates client is active")
                except Exception:
                    description = "another getUpdates client is active"
                print("TELEGRAM_CONFLICT=", description, flush=True)
                print("Stop the other Colab/bot process using this same Telegram token.", flush=True)
                time.sleep(10)
                continue
            poll.raise_for_status()
            result = poll.json()
            if not result.get("ok"):
                raise RuntimeError(f"Telegram getUpdates failed: {result}")

            for update in result.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message") or {}
                chat = (msg.get("chat") or {}).get("id")
                text = (msg.get("text") or "").strip()
                if not chat or not text:
                    continue
                print("TELEGRAM_RX=PASS", flush=True)
                if text.startswith("/start"):
                    send(
                        chat,
                        "أرسل موضوع الفيديو فقط، مثال: فوائد الذكاء الاصطناعي في الدراسة",
                    )
                    continue
                topic = re.sub(
                    r"^(اعملي|اعمل|اصنع|أنشئ)\s+(لي\s+)?فيديو\s+(عن\s+)?",
                    "",
                    text,
                ).strip() or text
                try:
                    make_video(chat, topic)
                except Exception as exc:
                    send(chat, "تعذر إنشاء الفيديو: " + str(exc)[:700])
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print("poll error:", type(exc).__name__, str(exc)[:500], flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
