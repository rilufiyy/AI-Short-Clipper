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
            text="Masukkan API key → provider terdeteksi otomatis, atau pilih manual.",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        # Row 1: key input
        input_row = ctk.CTkFrame(qs_inner, fg_color="transparent")
        input_row.pack(fill="x", pady=(0, 6))

        self._qs_entry = ctk.CTkEntry(
            input_row,
            placeholder_text="Tempel API key di sini…",
            show="•",
            font=ctk.CTkFont(size=11),
            height=36,
        )
        self._qs_entry.pack(fill="x")
        self._qs_entry.bind("<KeyRelease>", self._qs_on_type)

        # Row 2: provider selector + apply button
        action_row = ctk.CTkFrame(qs_inner, fg_color="transparent")
        action_row.pack(fill="x")

        self._qs_provider_var = ctk.StringVar(value="Auto")
        self._qs_seg = ctk.CTkSegmentedButton(
            action_row,
            values=["Auto", "Gemini", "OpenAI"],
            variable=self._qs_provider_var,
            font=ctk.CTkFont(size=10),
            height=34,
        )
        self._qs_seg.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            action_row,
            text="Apply ke Semua  ✓",
            height=34,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._qs_apply,
        ).pack(side="left", fill="x", expand=True)

        self._qs_status = ctk.CTkLabel(
            qs_inner, text="",
            font=ctk.CTkFont(size=10, weight="bold"),
            anchor="w",
        )
        self._qs_status.pack(fill="x", pady=(4, 0))

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
            return
        provider = detect_provider(key)
        if provider == "gemini":
            self._qs_status.configure(text="✓ Gemini terdeteksi", text_color="#2a8a4a")
            self._qs_provider_var.set("Gemini")
        elif provider == "openai":
            self._qs_status.configure(text="✓ OpenAI terdeteksi", text_color="#3a8fd1")
            self._qs_provider_var.set("OpenAI")
        else:
            self._qs_status.configure(text="Format tidak dikenali — pilih provider di atas lalu Apply", text_color="orange")
            self._qs_provider_var.set("Auto")

    def _qs_apply(self):
        from utils.gemini_client import detect_provider, GEMINI_API_BASE
        key = self._qs_entry.get().strip()
        if not key or len(key) < 10:
            self._qs_status.configure(text="API key tidak valid.", text_color="#e05555")
            return

        seg_val = self._qs_provider_var.get()
        if seg_val == "Gemini":
            provider = "gemini"
        elif seg_val == "OpenAI":
            provider = "openai"
        else:
            provider = detect_provider(key)

        if provider == "unknown":
            self._qs_status.configure(text="Pilih Gemini atau OpenAI di segmented button dulu.", text_color="orange")
            return

        if provider == "gemini":
            new_providers = {
                "highlight_finder":    {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "api_key": key, "model": "gemini-2.5-flash"},
                "youtube_title_maker": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "api_key": key, "model": "gemini-2.5-flash"},
                "caption_maker":       {"base_url": GEMINI_API_BASE, "api_key": key, "model": "gemini-2.5-flash"},
                "hook_maker":          {"base_url": GEMINI_API_BASE, "api_key": key, "model": "gemini-3.1-flash-tts-preview"},
            }
        else:
            new_providers = {
                "highlight_finder":    {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "gpt-4.1"},
                "youtube_title_maker": {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "gpt-4.1"},
                "caption_maker":       {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "whisper-1"},
                "hook_maker":          {"base_url": "https://api.openai.com/v1", "api_key": key, "model": "tts-1"},
            }

        # ConfigManager wraps the real dict in .config; plain dict works directly
        raw_cfg = self.config.config if hasattr(self.config, 'config') else self.config
        existing = raw_cfg.setdefault("ai_providers", {})
        for pkey, pval in new_providers.items():
            existing.setdefault(pkey, {}).update(pval)

        if self.on_save_callback:
            self.on_save_callback(raw_cfg)

        for pk in ("highlight_finder", "caption_maker", "hook_maker", "youtube_title_maker"):
            self._update_status(pk)

        name = "Gemini" if provider == "gemini" else "OpenAI"
        self._qs_status.configure(text=f"✓ Semua provider dikonfigurasi dengan {name}!", text_color="#2a8a4a")
        self._qs_entry.delete(0, "end")
        self._qs_provider_var.set("Auto")

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
