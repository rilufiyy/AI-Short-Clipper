"""
Telegram Notifier - Send processing completion notifications via Telegram Bot API.

Credentials (bot_token, chat_id) are stored in config.json on the user's local
machine. They are NEVER embedded in the EXE binary.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime


_API_BASE = "https://api.telegram.org/bot{token}/{method}"


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


def notify_clips_complete(config: dict, highlights: list, video_info: dict,
                           drive_uploaded: bool = False,
                           start_time: datetime = None) -> bool:
    """Send a 'clips done' notification. Returns True on success, False on failure."""
    tg = config.get("telegram", {})
    token = tg.get("bot_token", "").strip()
    chat_id = tg.get("chat_id", "").strip()

    if not (token and chat_id):
        return False

    video_title = video_info.get("title", "Unknown") if video_info else "Unknown"
    n = len(highlights)

    # Build clip list
    clip_lines = []
    for i, h in enumerate(highlights, 1):
        title = h.get("title", f"Clip {i}")
        score = h.get("virality_score", "")
        score_str = f" [{score}/10]" if score else ""
        clip_lines.append(f"  {i}. {title}{score_str}")

    clips_text = "\n".join(clip_lines) if clip_lines else "  (tidak ada clip)"

    # Duration info
    duration_str = ""
    if start_time:
        secs = int((datetime.now() - start_time).total_seconds())
        m, s = divmod(secs, 60)
        duration_str = f"\n⏱ Waktu proses: {m}m {s}s"

    drive_str = "\n☁️ Di-upload ke Google Drive ✓" if drive_uploaded else ""

    text = (
        f"✅ <b>YT Short Clipper — Selesai!</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📹 <b>Video:</b> {video_title}\n"
        f"🎬 <b>{n} clip berhasil dibuat:</b>\n"
        f"{clips_text}"
        f"{drive_str}"
        f"{duration_str}\n"
        f"━━━━━━━━━━━━━━━━\n"
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