"""
Daily usage quota tracker.
Limits how many full video-clip generations a user can run per day,
with a configurable reset hour.

Data stored in: <app_dir>/usage_tracker.json
"""

import json
import os
from datetime import datetime, timedelta


_TRACKER_FILE = "usage_tracker.json"
DEFAULT_MAX_DAILY = 2    # max clip sessions per reset period
DEFAULT_RESET_HOUR = 0   # 00:00 midnight


def _tracker_path() -> str:
    from utils.helpers import get_app_dir
    return os.path.join(get_app_dir(), _TRACKER_FILE)


def _load() -> dict:
    try:
        with open(_tracker_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"count": 0, "last_reset": None}


def _save(data: dict) -> None:
    with open(_tracker_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _next_reset_dt(reset_hour: int) -> datetime:
    """Datetime of the next upcoming reset at reset_hour:00."""
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
    # Next reset after the last reset moment
    nxt = last.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    if nxt <= last:
        nxt += timedelta(days=1)
    return datetime.now() >= nxt


def _fmt_remaining(reset_hour: int) -> str:
    diff = _next_reset_dt(reset_hour) - datetime.now()
    h = int(diff.total_seconds() // 3600)
    m = int((diff.total_seconds() % 3600) // 60)
    if h > 0:
        return f"{h} jam {m} menit"
    return f"{m} menit"


# ── Public API ────────────────────────────────────────────────────────────────

def check_quota(max_uses: int = DEFAULT_MAX_DAILY,
                reset_hour: int = DEFAULT_RESET_HOUR) -> tuple:
    """
    Returns (allowed: bool, message: str).
    Resets count automatically if the reset window has passed.
    """
    data = _load()

    if _should_reset(data.get("last_reset"), reset_hour):
        data["count"] = 0
        data["last_reset"] = datetime.now().isoformat()
        _save(data)

    count = data.get("count", 0)
    if count >= max_uses:
        remaining = _fmt_remaining(reset_hour)
        reset_time = _next_reset_dt(reset_hour).strftime("%H:%M")
        msg = (
            f"Kuota harian kamu sudah habis!\n\n"
            f"Terpakai: {count}/{max_uses} generate hari ini.\n"
            f"Kuota direset pukul {reset_time} ({remaining} lagi).\n\n"
            f"Upgrade ke API berbayar untuk penggunaan tak terbatas."
        )
        return False, msg

    sisa = max_uses - count - 1
    return True, f"Sisa kuota setelah ini: {sisa} generate."


def increment() -> None:
    """Call this after a successful clip generation session completes."""
    data = _load()
    data["count"] = data.get("count", 0) + 1
    if not data.get("last_reset"):
        data["last_reset"] = datetime.now().isoformat()
    _save(data)


def get_status_text(max_uses: int = DEFAULT_MAX_DAILY,
                    reset_hour: int = DEFAULT_RESET_HOUR) -> str:
    """Short status string for display in the UI."""
    data = _load()
    if _should_reset(data.get("last_reset"), reset_hour):
        count = 0
    else:
        count = data.get("count", 0)
    reset_time = _next_reset_dt(reset_hour).strftime("%H:%M")
    return f"{count}/{max_uses} generate dipakai hari ini • Reset pukul {reset_time}"


def reset_quota() -> None:
    """Manually reset quota (for admin/testing)."""
    _save({"count": 0, "last_reset": datetime.now().isoformat()})