"""
First-run API Key Setup Dialog
Auto-detects provider from key format (AIza* = Gemini, sk-* = OpenAI)
and configures all 4 processing steps accordingly.
"""

import webbrowser
import customtkinter as ctk

GEMINI_KEY_URL = "https://aistudio.google.com/app/apikey"
OPENAI_KEY_URL = "https://platform.openai.com/api-keys"

_PROVIDER_COLORS = {
    "gemini": ("#2a8a4a", "#1e6b38"),   # green
    "openai": ("#1a6fa8", "#145a87"),   # blue
    "unknown": ("#555", "#444"),
}
_PROVIDER_LABELS = {
    "gemini": "✓ Gemini Free Tier terdeteksi",
    "openai": "✓ OpenAI terdeteksi",
    "unknown": "",
}


class APISetupDialog(ctk.CTkToplevel):
    """First-run dialog to set up API key — auto-detects Gemini or OpenAI."""

    def __init__(self, parent, config_manager, on_done_callback=None):
        super().__init__(parent)

        self.config_manager = config_manager
        self.on_done_callback = on_done_callback
        self._key_visible = False
        self._detected = "unknown"

        self.title("Setup API Key")
        self.geometry("500x470")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_skip)

        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 235
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()
        self.after(100, self._grab_focus)

    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
            self.key_entry.focus_set()
        except Exception:
            pass

    def _build_ui(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=20)

        # Header
        ctk.CTkLabel(main, text="🔑", font=ctk.CTkFont(size=36)).pack(pady=(0, 4))
        ctk.CTkLabel(
            main, text="Setup API Key",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            main,
            text="Masukkan API key — app akan otomatis mendeteksi provider kamu",
            font=ctk.CTkFont(size=11),
            text_color=("#888", "#888"),
        ).pack(pady=(0, 12))

        # Provider options card
        card = ctk.CTkFrame(
            main,
            fg_color=("#1f1f1f", "#141414"),
            corner_radius=10,
            border_width=1,
            border_color=("#2f2f2f", "#222222"),
        )
        card.pack(fill="x", pady=(0, 10))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=14, pady=10)
        row.grid_columnconfigure((0, 1), weight=1, uniform="opt")

        # Gemini option
        gem = ctk.CTkFrame(row, fg_color=("#2a2a2a", "#1a1a1a"), corner_radius=8)
        gem.grid(row=0, column=0, padx=(0, 5), sticky="nsew")
        ctk.CTkLabel(gem, text="🟢 Gemini", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(
            gem, text="Free tier\nKey: AIza…",
            font=ctk.CTkFont(size=9), text_color="gray", justify="center",
        ).pack(pady=(0, 4))
        ctk.CTkButton(
            gem, text="Dapatkan Key →", height=26, font=ctk.CTkFont(size=9),
            fg_color=("#3a8fd1", "#2a6fab"), hover_color=("#2a7ab8", "#1e5a8a"),
            command=lambda: webbrowser.open(GEMINI_KEY_URL),
        ).pack(padx=8, pady=(0, 10), fill="x")

        # OpenAI option
        oai = ctk.CTkFrame(row, fg_color=("#2a2a2a", "#1a1a1a"), corner_radius=8)
        oai.grid(row=0, column=1, padx=(5, 0), sticky="nsew")
        ctk.CTkLabel(oai, text="🔴 OpenAI", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(8, 2))
        ctk.CTkLabel(
            oai, text="Berbayar\nKey: sk-…",
            font=ctk.CTkFont(size=9), text_color="gray", justify="center",
        ).pack(pady=(0, 4))
        ctk.CTkButton(
            oai, text="Dapatkan Key →", height=26, font=ctk.CTkFont(size=9),
            fg_color=("#555", "#444"), hover_color=("#666", "#555"),
            command=lambda: webbrowser.open(OPENAI_KEY_URL),
        ).pack(padx=8, pady=(0, 10), fill="x")

        # Key input row
        input_row = ctk.CTkFrame(main, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 6))

        self.key_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Tempel API key kamu di sini…",
            show="•",
            font=ctk.CTkFont(size=12),
            height=38,
        )
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.key_entry.bind("<KeyRelease>", self._on_key_typed)

        self.toggle_btn = ctk.CTkButton(
            input_row,
            text="Lihat", width=52, height=38,
            font=ctk.CTkFont(size=11),
            fg_color=("#3a3a3a", "#2a2a2a"),
            hover_color=("#4a4a4a", "#3a3a3a"),
            command=self._toggle_visibility,
        )
        self.toggle_btn.pack(side="left")

        # Detected provider badge
        self.detect_label = ctk.CTkLabel(
            main, text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#2a8a4a",
        )
        self.detect_label.pack(pady=(0, 4))

        # Error label
        self.error_label = ctk.CTkLabel(
            main, text="",
            font=ctk.CTkFont(size=10),
            text_color="#e05555",
        )
        self.error_label.pack(pady=(0, 4))

        # Action buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame, text="Lewati", width=120, height=40,
            font=ctk.CTkFont(size=12),
            fg_color=("#3a3a3a", "#2a2a2a"),
            hover_color=("#4a4a4a", "#3a3a3a"),
            command=self._on_skip,
        ).pack(side="left")

        self.save_btn = ctk.CTkButton(
            btn_frame, text="Simpan & Mulai  ✓",
            height=40, font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_save,
        )
        self.save_btn.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def _on_key_typed(self, _event=None):
        from utils.gemini_client import detect_provider
        key = self.key_entry.get().strip()
        self.error_label.configure(text="")
        if len(key) < 4:
            self.detect_label.configure(text="")
            self._detected = "unknown"
            return
        self._detected = detect_provider(key)
        label = _PROVIDER_LABELS.get(self._detected, "")
        color = _PROVIDER_COLORS.get(self._detected, ("#555", "#444"))[0]
        self.detect_label.configure(text=label, text_color=color)

    def _toggle_visibility(self):
        self._key_visible = not self._key_visible
        self.key_entry.configure(show="" if self._key_visible else "•")
        self.toggle_btn.configure(text="Sembunyikan" if self._key_visible else "Lihat")

    def _on_save(self):
        key = self.key_entry.get().strip()
        if not key:
            self.error_label.configure(text="API key tidak boleh kosong.")
            return
        if len(key) < 10:
            self.error_label.configure(text="API key terlalu pendek, cek lagi.")
            return

        from utils.gemini_client import get_provider_configs
        configs = get_provider_configs(key)

        cfg = self.config_manager.config
        providers = cfg.setdefault("ai_providers", {})
        for pkey, pval in configs.items():
            providers.setdefault(pkey, {}).update(pval)

        self.config_manager.save()
        self._close()

    def _on_skip(self):
        self._close()

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if self.on_done_callback:
            try:
                self.on_done_callback()
            except Exception:
                pass