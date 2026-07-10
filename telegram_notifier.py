"""
Telegram Notifier - Send processing completion notifications via Telegram Bot API.

Bot token is pre-configured (shared bot). Users only need to set their chat_id
by sending /start to the bot and clicking "Ambil Chat ID" in settings.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime


_API_BASE = "https://api.telegram.org/bot{token}/{method}"

# Load shared bot credentials from secrets.json (gitignored)
def _load_secrets() -> dict:
    import sys
    from pathlib import Path
    base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    secrets_path = base / "secrets.json"
    try:
        with open(secrets_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

_secrets = _load_secrets()
DEFAULT_BOT_TOKEN = _secrets.get("telegram_bot_token", "")
DEFAULT_CHAT_ID = _secrets.get("telegram_chat_id", "")

def _call(token: str, method: str, payload: dict) -> dict:
    """Make a Telegram Bot API call. Returns parsed JSON response."""
    url = _API_BASE.format(token=token, method=method)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise Exception(f"Telegram API error {e.code}: {body}")


def send_message(bot_token: str, chat_id: str, text: str,
                 parse_mode: str = "HTML") -> dict:
    """Send a plain text message to a chat."""
    return _call(bot_token, "sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    })


def get_updates(bot_token: str, limit: int = 10) -> list:
    """Return the latest updates (used to find chat_id after user messages bot)."""
    result = _call(bot_token, "getUpdates", {"limit": limit, "timeout": 0})
    return result.get("result", [])


def get_recent_chat_ids(bot_token: str) -> list[dict]:
    """Return distinct {chat_id, name} pairs from recent updates."""
    updates = get_updates(bot_token)
    seen = {}
    for upd in updates:
        msg = upd.get("message") or upd.get("channel_post") or {}
        chat = msg.get("chat", {})
        cid = chat.get("id")
        if cid and cid not in seen:
            name = (
                chat.get("title")
                or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                or str(cid)
            )
            seen[cid] = {"chat_id": str(cid), "name": name, "type": chat.get("type", "")}
    return list(seen.values())


def is_configured(config: dict) -> bool:
    """Return True if Telegram notifications are enabled and credentials are set."""
    tg = config.get("telegram", {})
    return bool(
        tg.get("enabled", False)
        and tg.get("bot_token", "").strip()
        and tg.get("chat_id", "").strip()
    )


def _parse_duration(start: str, end: str) -> str:
    """Calculate clip duration from timestamp strings (HH:MM:SS,mmm or HH:MM:SS)."""
    try:
        def to_secs(ts: str) -> float:
            ts = ts.replace(",", ".").strip()
            parts = ts.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            return 0.0
        secs = int(to_secs(end) - to_secs(start))
        return f"{secs}s" if secs < 60 else f"{secs // 60}m{secs % 60:02d}s"
    except Exception:
        return ""


def notify_clips_complete(config: dict, highlights: list, video_info: dict,
                           drive_uploaded: bool = False,
                           start_time: datetime = None,
                           output_folder: str = "") -> bool:
    """Send a 'clips done' notification. Returns True on success, False on failure."""
    tg = config.get("telegram", {})
    token = tg.get("bot_token", "").strip()
    chat_id = tg.get("chat_id", "").strip()

    if not (token and chat_id):
        return False

    video_info = video_info or {}
    video_title = video_info.get("title", "Unknown")
    channel = video_info.get("channel") or video_info.get("uploader", "")
    video_url = video_info.get("webpage_url") or video_info.get("url", "")
    n = len(highlights)

    # Build clip list — title, duration, virality, hook
    clip_lines = []
    for i, h in enumerate(highlights, 1):
        title = h.get("title", f"Clip {i}")
        score = h.get("virality_score", "")
        hook = h.get("hook_text", "")
        dur = _parse_duration(h.get("start_time", ""), h.get("end_time", ""))

        score_str = f"⭐{score}/10" if score else ""
        dur_str = f"⏳{dur}" if dur else ""
        meta = "  ".join(filter(None, [score_str, dur_str]))

        clip_lines.append(f"\n<b>{i}. {title}</b>")
        if meta:
            clip_lines.append(f"  {meta}")
        if hook:
            clip_lines.append(f"  💬 <i>{hook}</i>")

    clips_text = "\n".join(clip_lines) if clip_lines else "  (tidak ada clip)"

    # Processing time
    duration_str = ""
    if start_time:
        secs = int((datetime.now() - start_time).total_seconds())
        m, s = divmod(secs, 60)
        duration_str = f"\n⏱ <b>Waktu proses:</b> {m}m {s}s"

    # Extra info lines
    channel_str = f"\n👤 <b>Channel:</b> {channel}" if channel else ""
    url_str = f"\n🔗 <a href=\"{video_url}\">Buka video YouTube</a>" if video_url else ""
    folder_str = f"\n📂 <b>Folder:</b> <code>{output_folder}</code>" if output_folder else ""
    drive_str = "\n☁️ Di-upload ke Google Drive ✓" if drive_uploaded else ""

    text = (
        f"✅ <b>YT Short Clipper — Selesai!</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📹 <b>{video_title}</b>"
        f"{channel_str}"
        f"{url_str}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎬 <b>{n} clip berhasil dibuat:</b>"
        f"{clips_text}\n"
        f"━━━━━━━━━━━━━━━━"
        f"{folder_str}"
        f"{drive_str}"
        f"{duration_str}\n"
        f"<i>{datetime.now().strftime('%d %b %Y %H:%M')}</i>"
    )

    try:
        send_message(token, chat_id, text)
        return True
    except Exception as e:
        print(f"[Telegram] Notification failed: {e}")
        return False


def notify_error(config: dict, video_url: str, error_msg: str) -> bool:
    """Send an error notification. Returns True on success."""
    tg = config.get("telegram", {})
    token = tg.get("bot_token", "").strip()
    chat_id = tg.get("chat_id", "").strip()

    if not (token and chat_id):
        return False

    text = (
        f"❌ <b>YT Short Clipper — Gagal!</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🔗 URL: {video_url or '-'}\n"
        f"⚠️ Error: <code>{error_msg[:300]}</code>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<i>{datetime.now().strftime('%d %b %Y %H:%M')}</i>"
    )

    try:
        send_message(token, chat_id, text)
        return True
    except Exception as e:
        print(f"[Telegram] Error notification failed: {e}")
        return False
