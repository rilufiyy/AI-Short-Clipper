"""
First-run API Key Setup Dialog
Shows once when highlight_finder api_key is empty, guides user to set up Gemini Free Tier.
"""

import webbrowser
import customtkinter as ctk

GEMINI_KEY_URL = "https://aistudio.google.com/app/apikey"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
GEMINI_MODEL = "gemini-2.5-flash"


class APISetupDialog(ctk.CTkToplevel):
    """First-run dialog to set up Gemini API key."""

    def __init__(self, parent, config_manager, on_done_callback=None):
        super().__init__(parent)

        self.config_manager = config_manager
        self.on_done_callback = on_done_callback
        self._key_visible = False

        self.title("Setup API Key")
        self.geometry("500x430")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self._on_skip)

        self.update_idletasks()
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 215
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
        ctk.CTkLabel(
            main, text="🔑",
            font=ctk.CTkFont(size=36),
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            main, text="Setup API Key Dulu",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            main,
            text="Gunakan Gemini Free Tier — gratis, tanpa kartu kredit",
            font=ctk.CTkFont(size=11),
            text_color=("#888", "#888"),
        ).pack(pady=(0, 14))

        # Steps card
        card = ctk.CTkFrame(
            main,
            fg_color=("#1f1f1f", "#141414"),
            corner_radius=10,
            border_width=1,
            border_color=("#2f2f2f", "#222222"),
        )
        card.pack(fill="x", pady=(0, 12))

        steps_text = (
            "1. Klik tombol di bawah → buka Google AI Studio\n"
            "2. Login dengan akun Google kamu\n"
            "3. Klik \"Create API Key\" → salin key-nya\n"
            "4. Tempel di kolom input di bawah ini"
        )
        ctk.CTkLabel(
            card,
            text=steps_text,
            font=ctk.CTkFont(size=11),
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=16, pady=12)

        # Open AI Studio button
        ctk.CTkButton(
            card,
            text="Buka Google AI Studio  →",
            font=ctk.CTkFont(size=11),
            height=30,
            fg_color=("#3a8fd1", "#2a6fab"),
            hover_color=("#2a7ab8", "#1e5a8a"),
            command=lambda: webbrowser.open(GEMINI_KEY_URL),
        ).pack(padx=16, pady=(0, 14))

        # Key input row
        input_row = ctk.CTkFrame(main, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 14))

        self.key_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Tempel API key kamu di sini…",
            show="•",
            font=ctk.CTkFont(size=12),
            height=38,
        )
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.toggle_btn = ctk.CTkButton(
            input_row,
            text="Lihat",
            width=52,
            height=38,
            font=ctk.CTkFont(size=11),
            fg_color=("#3a3a3a", "#2a2a2a"),
            hover_color=("#4a4a4a", "#3a3a3a"),
            command=self._toggle_visibility,
        )
        self.toggle_btn.pack(side="left")

        # Error label (hidden until needed)
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
            btn_frame,
            text="Lewati",
            width=120,
            height=40,
            font=ctk.CTkFont(size=12),
            fg_color=("#3a3a3a", "#2a2a2a"),
            hover_color=("#4a4a4a", "#3a3a3a"),
            command=self._on_skip,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="Simpan & Mulai  ✓",
            height=40,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_save,
        ).pack(side="right", fill="x", expand=True, padx=(10, 0))

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

        cfg = self.config_manager.config
        providers = cfg.setdefault("ai_providers", {})

        # Apply Gemini key + config to LLM providers only
        for provider_key in ("highlight_finder", "youtube_title_maker"):
            p = providers.setdefault(provider_key, {})
            p["api_key"] = key
            p["base_url"] = GEMINI_BASE_URL
            p["model"] = GEMINI_MODEL

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