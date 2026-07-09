"""
Daily usage quota tracker — per-provider counters.
Each provider (gemini, openai, etc.) has its own independent daily quota.

Data stored in: <app_dir>/usage_tracker.json
Format: {"gemini": {"count": 1, "last_reset": "..."}, "openai": {"count": 0, ...}}
"""

import json
import os
from datetime import datetime, timedelta


_TRACKER_FILE = "usage_tracker.json"

PROVIDER_LIMITS = {
    "gemini":  {"max_uses": 10, "label": "Gemini Free Tier"},
    "openai":  {"max_uses": 10, "label": "OpenAI"},
    "default": {"max_uses": 10, "label": "AI"},
}
DEFAULT_RESET_HOUR = 0   # 00:00 midnight


def _tracker_path() -> str:
    from utils.helpers import get_app_dir
    return os.path.join(get_app_dir(), _TRACKER_FILE)


def _load() -> dict:
    try:
        with open(_tracker_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    with open(_tracker_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _next_reset_dt(reset_hour: int) -> datetime:
    now = datetime.now()
    t = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    if t <= now:
        t += timedelta(days=1)
    return t


def _should_reset(last_reset_str, reset_hour: int) -> bool:
    if not last_reset_str:
        return True
    try:
        last = datetime.fromisoformat(last_reset_str)
    except Exception:
        return True
    nxt = last.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    if nxt <= last:
        nxt += timedelta(days=1)
    return datetime.now() >= nxt


def _fmt_remaining(reset_hour: int) -> str:
    diff = _next_reset_dt(reset_hour) - datetime.now()
    h = int(diff.total_seconds() // 3600)
    m = int((diff.total_seconds() % 3600) // 60)
    return f"{h} jam {m} menit" if h > 0 else f"{m} menit"


# ── Public API ────────────────────────────────────────────────────────────────

def check_quota(provider: str = "default",
                reset_hour: int = DEFAULT_RESET_HOUR) -> tuple:
    """
    Returns (allowed: bool, message: str).
    Checks quota for the given provider independently.
    """
    cfg = PROVIDER_LIMITS.get(provider, PROVIDER_LIMITS["default"])
    max_uses = cfg["max_uses"]
    label    = cfg["label"]

    data = _load()
    entry = data.get(provider, {"count": 0, "last_reset": None})

    if _should_reset(entry.get("last_reset"), reset_hour):
        entry = {"count": 0, "last_reset": datetime.now().isoformat()}
        data[provider] = entry
        _save(data)

    count = entry.get("count", 0)
    if count >= max_uses:
        remaining  = _fmt_remaining(reset_hour)
        reset_time = _next_reset_dt(reset_hour).strftime("%H:%M")
        msg = (
            f"Kuota harian {label} kamu sudah habis!\n\n"
            f"Terpakai: {count}/{max_uses} generate hari ini.\n"
            f"Kuota direset pukul {reset_time} ({remaining} lagi).\n\n"
            f"Upgrade ke API berbayar untuk penggunaan tak terbatas."
        )
        return False, msg

    return True, f"Sisa kuota {label} setelah ini: {max_uses - count - 1} generate."


def increment(provider: str = "default",
              reset_hour: int = DEFAULT_RESET_HOUR) -> None:
    """Increment usage count for the given provider after successful generation."""
    data  = _load()
    entry = data.get(provider, {"count": 0, "last_reset": None})

    if _should_reset(entry.get("last_reset"), reset_hour):
        entry = {"count": 0, "last_reset": datetime.now().isoformat()}

    entry["count"] = entry.get("count", 0) + 1
    if not entry.get("last_reset"):
        entry["last_reset"] = datetime.now().isoformat()
    data[provider] = entry
    _save(data)


def get_status_text(provider: str = "default",
                    reset_hour: int = DEFAULT_RESET_HOUR) -> str:
    """Short status string for logs/UI."""
    cfg   = PROVIDER_LIMITS.get(provider, PROVIDER_LIMITS["default"])
    data  = _load()
    entry = data.get(provider, {"count": 0, "last_reset": None})
    count = 0 if _should_reset(entry.get("last_reset"), reset_hour) else entry.get("count", 0)
    reset_time = _next_reset_dt(reset_hour).strftime("%H:%M")
    return f"[{cfg['label']}] {count}/{cfg['max_uses']} generate dipakai • Reset {reset_time}"


def reset_quota(provider: str = None) -> None:
    """Manually reset quota. Pass provider name or None to reset all."""
    data = _load()
    if provider:
        data[provider] = {"count": 0, "last_reset": datetime.now().isoformat()}
    else:
        for p in list(data.keys()):
            data[p] = {"count": 0, "last_reset": datetime.now().isoformat()}
    _save(data)