"""
AI API Settings Sub-Page - Card-based navigation to individual providers
"""

import customtkinter as ctk

from pages.settings.base_dialog import BaseSettingsSubPage


class AIAPISettingsSubPage(BaseSettingsSubPage):
    """Sub-page for AI API settings with card navigation"""
    
    def __init__(self, parent, config, on_save_callback, on_back_callback):
        self.config = config
        self.on_save_callback = on_save_callback
        self.main_back = on_back_callback
        self.container = parent
        
        super().__init__(parent, "AI API Settings", on_back_callback)
        
        self.create_content()
    
    def create_content(self):
        """Create page content with provider cards - NO Provider Type buttons here"""
        # ── Quick Setup Section ────────────────────────────────────────────
        qs_section = self.create_section("Setup Cepat — Satu Key untuk Semua")

        qs_inner = ctk.CTkFrame(qs_section, fg_color="transparent")
        qs_inner.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkLabel(
            qs_inner,
            text="Masukkan 1 API key → otomatis dikonfigurasi ke semua provider yang kompatibel.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        input_row = ctk.CTkFrame(qs_inner, fg_color="transparent")
        input_row.pack(fill="x")

        self._qs_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Tempel API key (AIza… untuk Gemini, sk-… untuk OpenAI)…",
            show="•",
            font=ctk.CTkFont(size=11),
            height=36,
        )
        self._qs_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._qs_entry.bind("<KeyRelease>", self._qs_on_type)

        self._qs_apply_btn = ctk.CTkButton(
            input_row,
            text="Apply ke Semua",
            width=130, height=36,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._qs_apply,
        )
        self._qs_apply_btn.pack(side="left")

        self._qs_status = ctk.CTkLabel(
            qs_inner, text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            anchor="w",
        )
        self._qs_status.pack(fill="x", pady=(4, 0))

        # Manual provider selector (shown only when key format is unknown)
        self._qs_manual_frame = ctk.CTkFrame(qs_inner, fg_color="transparent")
        ctk.CTkButton(
            self._qs_manual_frame,
            text="Apply sebagai Gemini",
            height=30, font=ctk.CTkFont(size=10),
            fg_color=("#2a6fab", "#1e5a8a"),
            hover_color=("#1e5a8a", "#174a72"),
            command=lambda: self._qs_apply(force_provider="gemini"),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            self._qs_manual_frame,
            text="Apply sebagai OpenAI",
            height=30, font=ctk.CTkFont(size=10),
            fg_color=("#555", "#444"),
            hover_color=("#666", "#555"),
            command=lambda: self._qs_apply(force_provider="openai"),
        ).pack(side="left")
        # Register in geometry manager first, then hide
        self._qs_manual_frame.pack(fill="x", pady=(4, 0))
        self._qs_manual_frame.pack_forget()

        # ── AI Providers Section ───────────────────────────────────────────
        providers_section = self.create_section("AI Providers")

        cards_frame = ctk.CTkFrame(providers_section, fg_color="transparent")
        cards_frame.pack(fill="x", padx=10, pady=(0, 12))
        cards_frame.grid_columnconfigure((0, 1), weight=1, uniform="provider")
        
        # Row 1
        self._create_provider_card(cards_frame, 0, 0, "Highlight Finder", 
            "Find viral moments", "highlight_finder")
        self._create_provider_card(cards_frame, 0, 1, "Caption Maker", 
            "Generate captions", "caption_maker")
        
        # Row 2
        self._create_provider_card(cards_frame, 1, 0, "Hook Maker", 
            "Create TTS hooks", "hook_maker")
        self._create_provider_card(cards_frame, 1, 1, "Title Generator", 
            "Generate titles", "youtube_title_maker")
    
    def _create_provider_card(self, parent, row, col, title, desc, key):
        """Create a clickable provider card"""
        card = ctk.CTkFrame(parent, fg_color=("gray85", "gray20"), corner_radius=8, cursor="hand2")
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        card.bind("<Button-1>", lambda e, k=key: self.navigate_to_provider(k))
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(12, 5))
        header.bind("<Button-1>", lambda e, k=key: self.navigate_to_provider(k))
        
        ctk.CTkLabel(header, text=title, 
            font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
        
        status = ctk.CTkLabel(header, text="", font=ctk.CTkFont(size=10))
        status.pack(side="right")
        setattr(self, f"{key}_status", status)
        
        d = ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=9), text_color="gray")
        d.pack(anchor="w", padx=12, pady=(0, 5))
        d.bind("<Button-1>", lambda e, k=key: self.navigate_to_provider(k))
        
        m = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=9), text_color="gray")
        m.pack(anchor="w", padx=12, pady=(0, 12))
        m.bind("<Button-1>", lambda e, k=key: self.navigate_to_provider(k))
        setattr(self, f"{key}_model", m)
        
        card.bind("<Enter>", lambda e: card.configure(fg_color=("gray75", "gray25")))
        card.bind("<Leave>", lambda e: card.configure(fg_color=("gray85", "gray20")))
        
        self._update_status(key)
    
    def _update_status(self, key):
        """Update provider card status"""
        p = self.config.get("ai_providers", {}).get(key, {})
        api_key, model = p.get("api_key", ""), p.get("model", "")
        
        s = getattr(self, f"{key}_status", None)
        m = getattr(self, f"{key}_model", None)
        
        if s:
            if api_key and model:
                s.configure(text="Configured", text_color="green")
            elif api_key:
                s.configure(text="No model", text_color="orange")
            else:
                s.configure(text="Not set", text_color="gray")
        
        if m:
            m.configure(text=f"Model: {model}" if model else "Model: Not set")

    def _qs_on_type(self, _event=None):
        from utils.gemini_client import detect_provider
        key = self._qs_entry.get().strip()
        if len(key) < 4:
            self._qs_status.configure(text="", text_color="gray")
            self._qs_manual_frame.pack_forget()
            return
        provider = detect_provider(key)
        if provider == "gemini":
            self._qs_status.configure(text="✓ Gemini Free Tier terdeteksi — apply otomatis", text_color="#2a8a4a")
            self._qs_manual_frame.pack_forget()
        elif provider == "openai":
            self._qs_status.configure(text="✓ OpenAI terdeteksi — apply otomatis", text_color="#3a8fd1")
            self._qs_manual_frame.pack_forget()
        else:
            self._qs_status.configure(text="Format tidak dikenali — pilih provider manual:", text_color="orange")
            self._qs_manual_frame.pack(fill="x", pady=(4, 0))

    def _qs_apply(self, force_provider: str = None):
        from utils.gemini_client import get_provider_configs, detect_provider
        key = self._qs_entry.get().strip()
        if not key or len(key) < 10:
            self._qs_status.configure(text="API key tidak valid.", text_color="#e05555")
            return

        provider = force_provider or detect_provider(key)
        if provider == "unknown":
            self._qs_status.configure(text="Pilih provider di bawah dulu.", text_color="orange")
            return

        configs = get_provider_configs(key) if provider != "unknown" else {}
        if force_provider:
            # Override detection — rebuild configs with forced provider
            from utils.gemini_client import GEMINI_API_BASE
            if force_provider == "gemini":
                configs = {
                    "highlight_finder": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "api_key": key, "model": "gemini-2.5-flash"},
                    "youtube_title_maker": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "api_key": key, "model": "gemini-2.5-flash"},
                    "caption_maker": {"base_url": GEMINI_API_BASE, "api_key": key, "model": "gemini-2.5-flash"},
                    "hook_maker": {"base_url": GEMINI_API_BASE, "api_key": key, "model": "gemini-3.1-flash-tts-preview"},
                }
            else:
                configs = {
                    "highlight_finder": {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "gpt-4.1"},
                    "youtube_title_maker": {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "gpt-4.1"},
                    "caption_maker": {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "whisper-1"},
                    "hook_maker": {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "tts-1"},
                }

        providers = self.config.setdefault("ai_providers", {})
        for pkey, pval in configs.items():
            providers.setdefault(pkey, {}).update(pval)

        if self.on_save_callback:
            self.on_save_callback(self.config)

        for pk in ("highlight_finder", "caption_maker", "hook_maker", "youtube_title_maker"):
            self._update_status(pk)

        name = "Gemini" if provider == "gemini" else "OpenAI"
        self._qs_status.configure(
            text=f"✓ Semua provider dikonfigurasi dengan {name}!",
            text_color="#2a8a4a",
        )
        self._qs_manual_frame.pack_forget()
        self._qs_entry.delete(0, "end")

    def navigate_to_provider(self, key):
        """Navigate to provider settings page"""
        for w in self.container.winfo_children():
            w.destroy()
        
        if key == "highlight_finder":
            from pages.settings.ai_providers.highlight_finder import HighlightFinderSettingsPage
            HighlightFinderSettingsPage(self.container, self.config, self.on_save_callback, self._back)
        elif key == "caption_maker":
            from pages.settings.ai_providers.caption_maker import CaptionMakerSettingsPage
            CaptionMakerSettingsPage(self.container, self.config, self.on_save_callback, self._back)
        elif key == "hook_maker":
            from pages.settings.ai_providers.hook_maker import HookMakerSettingsPage
            HookMakerSettingsPage(self.container, self.config, self.on_save_callback, self._back)
        elif key == "youtube_title_maker":
            from pages.settings.ai_providers.title_generator import TitleGeneratorSettingsPage
            TitleGeneratorSettingsPage(self.container, self.config, self.on_save_callback, self._back)
    
    def _back(self):
        """Navigate back to AI API settings"""
        for w in self.container.winfo_children():
            w.destroy()
        AIAPISettingsSubPage(self.container, self.config, self.on_save_callback, self.main_back)
