"""
Google Drive Uploader - Auto-upload clip folders via rclone
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

RCLONE_REMOTE = "gdrive"
_WIN_FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class GDriveUploader:
    """Upload clip folders to Google Drive using rclone as backend."""

    def __init__(self, log_callback=None):
        self.log = log_callback or print

    # ------------------------------------------------------------------
    # rclone helpers
    # ------------------------------------------------------------------

    def _get_rclone(self) -> str:
        """Locate rclone: app folder first, then PATH."""
        import shutil
        local = APP_DIR / "rclone.exe"
        if local.exists():
            return str(local)
        found = shutil.which("rclone")
        if found:
            return found
        raise Exception(
            "rclone not found.\n"
            "Place rclone.exe in the app folder or add it to PATH."
        )

    def is_configured(self) -> bool:
        """True if rclone is available and 'gdrive' remote is set up."""
        try:
            rclone = self._get_rclone()
            r = subprocess.run(
                [rclone, "listremotes"],
                capture_output=True, text=True,
                timeout=10, creationflags=_WIN_FLAGS
            )
            return f"{RCLONE_REMOTE}:" in r.stdout
        except Exception:
            return False

    def is_authenticated(self) -> bool:
        """For rclone, configured == authenticated."""
        return self.is_configured()

    def authenticate(self, callback=None):
        """Not needed for rclone — auth is done via 'rclone config'."""
        if callback:
            callback("rclone: already authenticated via rclone config.")
        return True

    # ------------------------------------------------------------------
    # Session folder
    # ------------------------------------------------------------------

    def create_session_folder(self, root_folder_id: str, yt_title: str,
                               date_str: str = None) -> str:
        """Return the session folder *path* that will be created on Drive.

        rclone creates folders automatically when uploading — no explicit
        mkdir needed. Returns a nested path like '2026/06/12/Kajian-Slug'.
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month_names = ["Januari","Februari","Maret","April","Mei","Juni",
                       "Juli","Agustus","September","Oktober","November","Desember"]
        month = month_names[now.month - 1]
        day = now.strftime("%d")
        clean = re.sub(r'[<>:"/\\|?*\n\r\t]', '', yt_title).strip()
        clean = re.sub(r'[\s_]+', ' ', clean).strip()[:80].strip() or "video"
        folder_path = f"AI YT Clipper/{year}/{month}/{day}/{clean}"
        self.log(f"  [Drive] Session folder: {folder_path}")
        return folder_path

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_clip_folder(self, local_folder: Path, session_path: str,
                           clip_index: int = None, clip_title: str = None,
                           root_folder_id: str = "") -> str:
        """Upload clip files to Google Drive using rclone copy.

        Drive structure:
            [root_folder_id]/
            └── <session_path>/            ← e.g. "Podcast XYZ (2024-06-03)"
                └── Clip 01 — Title/
                    ├── master.mp4
                    ├── data.json
                    └── content.txt

        Args:
            local_folder   : path to clip folder on disk
            session_path   : session folder name returned by create_session_folder
            clip_index     : 1-based clip number
            clip_title     : clip title for folder name
            root_folder_id : Google Drive folder ID to treat as root
        """
        rclone = self._get_rclone()

        # Build readable clip folder name
        if clip_index is not None and clip_title:
            clean = re.sub(r'[<>:"/\\|?*\n\r\t]', '', clip_title).strip()[:60].strip()
            clip_folder_name = f"Clip {clip_index:02d} — {clean}"
        else:
            clip_folder_name = local_folder.name

        # Full destination path on the remote
        if session_path:
            dest_path = f"{session_path}/{clip_folder_name}"
        else:
            dest_path = clip_folder_name

        dest = f"{RCLONE_REMOTE}:{dest_path}"
        self.log(f"  [Drive] Uploading -> {dest_path}")

        # rclone copy with filter: skip temp files, only upload mp4/json/txt
        cmd = [
            rclone, "copy",
            str(local_folder),
            dest,
            "--filter", "- temp_*",
            "--filter", "+ *.mp4",
            "--filter", "+ *.json",
            "--filter", "+ *.txt",
            "--filter", "- *",
        ]
        if root_folder_id:
            cmd += ["--drive-root-folder-id", root_folder_id]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=1800, creationflags=_WIN_FLAGS
        )

        if result.returncode != 0:
            raise Exception(f"rclone upload failed:\n{result.stderr[:300]}")

        self.log("  [Drive] Upload selesai: master.mp4 + data.json + content.txt")
        return dest

    def set_folder_public(self, folder_id: str = ""):
        """Not applicable for rclone — manage permissions in Google Drive UI."""
        self.log("  [Drive] Folder permissions managed via Google Drive UI (rclone mode)")