"""
Base class for AI Provider settings pages
"""

import threading
import customtkinter as ctk
from tkinter import messagebox

from pages.settings.base_dialog import BaseSettingsSubPage


class BaseProviderSettingsPage(BaseSettingsSubPage):
    """Base class for AI provider settings pages"""
    
    # Override in child class for fixed model list (None = load from API)
    FIXED_MODELS = None
    # Override in child class to use manual input instead of dropdown
    USE_MANUAL_INPUT = False
    # Default model value when using manual input
    DEFAULT_MODEL = ""
    
    def __init__(self, parent, title, provider_key, config, on_save_callback, on_back_callback):
        self.config = config
        self.provider_key = provider_key
        self.on_save_callback = on_save_callback
        self.models_list = []
        
        super().__init__(parent, title, on_back_callback)
        
        self.create_provider_content()
        self.load_config()
    
    # Map provider key → (base_url, recommended_model, get_key_url, key_placeholder)
    _PROVIDER_PRESETS = {
        "gemini": (
            "https://generativelanguage.googleapis.com/v1beta/openai/",
            "gemini-2.5-flash",
            "https://ai.google.dev/gemini-api/docs/api-key",
            "AIza...",
        ),
        "openai": (
            "https://api.openai.com/v1",
            "gpt-5.4",
            "https://platform.openai.com",
            "sk-...",
        ),
        "ytclip": (
            "https://ai-api.ytclip.org/v1",
            "",
            "https://ai.ytclip.org",
            "ytc-...",
        ),
    }

    def create_provider_content(self):
        """Create provider settings content"""
        # Provider Type Section
        type_section = self.create_section("Provider Type")

        type_frame = ctk.CTkFrame(type_section, fg_color="transparent")
        type_frame.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(type_frame, text="Select API Provider", font=ctk.CTkFont(size=11)).pack(anchor="w")

        self.provider_type_var = ctk.StringVar(value="ytclip")
        self.provider_dropdown = ctk.CTkOptionMenu(type_frame,
            values=["🎬 YT CLIP AI", "🆓 Gemini Free Tier", "🤖 OpenAI", "⚙️ CUSTOM"],
            variable=self.provider_type_var, height=36,
            command=self._on_provider_type_changed)
        self.provider_dropdown.pack(fill="x", pady=(5, 0))

        # Info link — updates per provider
        self._provider_link_url = ""
        self.provider_info_label = ctk.CTkLabel(type_frame, text="",
            font=ctk.CTkFont(size=9), text_color=("#3B8ED0", "#5B9ED0"), cursor="hand2")
        self.provider_info_label.pack(anchor="w", pady=(4, 0))
        self.provider_info_label.bind("<Button-1>", self._open_provider_link)
        
        # System Message Section (optional, can be overridden by child)
        self.system_message_textbox = None
        
        # URL Section (only visible for custom)
        self.url_section = self.create_section("Base URL")
        self.url_section.pack_forget()  # Hidden by default
        
        url_frame = ctk.CTkFrame(self.url_section, fg_color="transparent")
        url_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkLabel(url_frame, text="API Base URL", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="https://api.openai.com/v1", height=36)
        self.url_entry.pack(fill="x", pady=(5, 0))
        
        # API Key Section
        key_section = self.create_section("API Key")
        
        key_frame = ctk.CTkFrame(key_section, fg_color="transparent")
        key_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkLabel(key_frame, text="API Key", font=ctk.CTkFont(size=11)).pack(anchor="w")
        self.key_entry = ctk.CTkEntry(key_frame, placeholder_text="sk- / AIza- ...", show="•", height=36)
        self.key_entry.pack(fill="x", pady=(5, 0))
        
        # Model Section
        self.model_section = self.create_section("Model")
        
        model_frame = ctk.CTkFrame(self.model_section, fg_color="transparent")
        model_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        ctk.CTkLabel(model_frame, text="Model Name", font=ctk.CTkFont(size=11)).pack(anchor="w")
        
        model_row = ctk.CTkFrame(model_frame, fg_color="transparent")
        model_row.pack(fill="x", pady=(5, 0))
        
        # Check if using manual input mode
        if self.USE_MANUAL_INPUT:
            # Manual input mode - use CTkEntry
            self.model_entry = ctk.CTkEntry(model_row, 
                placeholder_text=f"e.g., {self.DEFAULT_MODEL}", height=36)
            self.model_entry.pack(fill="x")
            self.model_dropdown = None
            self.model_var = None
            self.load_btn = None
        else:
            # Dropdown mode
            self.model_var = ctk.StringVar(value="")
            self.model_entry = None
            
            # Check if using fixed models or load from API
            if self.FIXED_MODELS:
                # Fixed dropdown - no load button needed
                self.model_dropdown = ctk.CTkOptionMenu(model_row, 
                    values=self.FIXED_MODELS,
                    variable=self.model_var, height=36)
                self.model_dropdown.pack(fill="x")
                self.load_btn = None
            else:
                # Dynamic dropdown with load button
                self.model_dropdown = ctk.CTkOptionMenu(model_row, 
                    values=["-- Click Load to fetch models --"],
                    variable=self.model_var, height=36, width=200)
                self.model_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 5))
                
                self.load_btn = ctk.CTkButton(model_row, text="🔄 Load", width=80, height=36,
                    command=self.load_models)
                self.load_btn.pack(side="right")
        
        # Actions
        actions_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(actions_frame, text="🔍 Validate Configuration", height=40,
            fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#36719F", "#144870"),
            command=self.validate_config).pack(fill="x", pady=(0, 10))
        
        # Save button
        self.create_save_button(self.save_settings)
    
    def _on_provider_type_changed(self, value):
        """Handle provider type dropdown change — auto-fill URL, model, and key hint."""
        if "CUSTOM" in value:
            self.url_section.pack(fill="x", pady=(0, 10), after=self.content.winfo_children()[1])
        else:
            self.url_section.pack_forget()

        ptype = self._get_provider_type_key()
        preset = self._PROVIDER_PRESETS.get(ptype)

        if preset:
            _, rec_model, key_url, key_hint = preset
            # Update provider info link
            if key_url:
                self.provider_info_label.configure(
                    text=f"Get free API key → {key_url.split('//')[1].split('/')[0]}")
                self._provider_link_url = key_url
            else:
                self.provider_info_label.configure(text="")
                self._provider_link_url = ""
            # Always auto-fill recommended model when user explicitly changes provider
            if rec_model and self.model_var is not None:
                self.model_var.set(rec_model)
                existing = list(self.model_dropdown.cget("values"))
                if rec_model not in existing:
                    clean = [v for v in existing if not v.startswith("--")]
                    self.model_dropdown.configure(values=[rec_model] + clean)
        else:
            self.provider_info_label.configure(text="")
            self._provider_link_url = ""

    def _auto_fill_model(self, model_name: str):
        """Set recommended model in the model dropdown/entry."""
        if self.model_var is not None:
            current = self.model_var.get()
            # Only auto-fill if empty or already a preset value (don't clobber user choice)
            preset_models = {v[1] for v in self._PROVIDER_PRESETS.values() if v[1]}
            if not current or current in preset_models or current.startswith("--"):
                self.model_var.set(model_name)
                existing = list(self.model_dropdown.cget("values"))
                if model_name not in existing:
                    clean = [v for v in existing if not v.startswith("--")]
                    self.model_dropdown.configure(values=[model_name] + clean)

    def _open_provider_link(self, event=None):
        """Open provider's API-key signup page in browser."""
        if self._provider_link_url:
            import webbrowser
            webbrowser.open(self._provider_link_url)

    def _update_provider_info(self, ptype: str):
        """Update info label for a provider key without triggering model auto-fill."""
        preset = self._PROVIDER_PRESETS.get(ptype)
        if preset:
            _, _, key_url, _ = preset
            if key_url:
                self.provider_info_label.configure(
                    text=f"Get free API key → {key_url.split('//')[1].split('/')[0]}")
                self._provider_link_url = key_url
                return
        self.provider_info_label.configure(text="")
        self._provider_link_url = ""

    def _get_provider_type_key(self):
        """Get provider type key from dropdown value"""
        value = self.provider_type_var.get()
        if "YT CLIP" in value:
            return "ytclip"
        elif "Gemini" in value:
            return "gemini"
        elif "OpenAI" in value or "OPEN AI" in value:
            return "openai"
        else:
            return "custom"

    def get_base_url(self):
        """Get base URL based on provider type"""
        ptype = self._get_provider_type_key()
        preset = self._PROVIDER_PRESETS.get(ptype)
        if preset:
            return preset[0]
        return self.url_entry.get().strip() or "https://api.openai.com/v1"
    
    def load_models(self):
        """Load available models from API"""
        if self.FIXED_MODELS:
            return  # No need to load for fixed models
            
        api_key = self.key_entry.get().strip()
        
        if not api_key:
            messagebox.showerror("Error", "Please enter API Key first")
            return
        
        url = self.get_base_url()
        self.load_btn.configure(state="disabled", text="Loading...")
        
        def do_load():
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key, base_url=url)
                models_response = client.models.list()
                models = [m.id for m in models_response.data]
                models.sort()
                
                self.after(0, lambda: self._on_models_loaded(models))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda msg=err_msg: self._on_models_error(msg))
        
        threading.Thread(target=do_load, daemon=True).start()
    
    def _on_models_loaded(self, models):
        """Handle models loaded"""
        self.load_btn.configure(state="normal", text="🔄 Load")
        self.models_list = models
        
        if models:
            # Update dropdown with loaded models
            self.model_dropdown.configure(values=models)
            # Keep current selection if valid, otherwise select first
            current = self.model_var.get()
            if current not in models:
                self.model_var.set(models[0])
            messagebox.showinfo("Success", f"Loaded {len(models)} models")
        else:
            messagebox.showwarning("Warning", "No models found")
    
    def _on_models_error(self, error):
        """Handle models load error"""
        self.load_btn.configure(state="normal", text="🔄 Load")
        messagebox.showerror("Error", f"Failed to load models:\n{error}")
    
    def validate_config(self):
        """Validate provider configuration"""
        api_key = self.key_entry.get().strip()
        model = self.model_var.get().strip()
        url = self.get_base_url()
        
        if not api_key:
            messagebox.showerror("Error", "API Key is required")
            return
        
        if not model or model.startswith("--"):
            messagebox.showerror("Error", "Please select a model")
            return
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=url)
            client.models.list()
            messagebox.showinfo("Success", f"✓ Configuration valid!\n\nModel: {model}\nURL: {url}")
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed:\n{str(e)}")
    
    def load_config(self):
        """Load config into UI"""
        # Handle both ConfigManager and dict
        if hasattr(self.config, 'config'):
            config_dict = self.config.config
        else:
            config_dict = self.config
            
        ai_providers = config_dict.get("ai_providers", {})
        provider = ai_providers.get(self.provider_key, {})
        
        # Determine provider type from saved URL
        base_url = provider.get("base_url", "")
        if "ytclip" in base_url:
            self.provider_type_var.set("🎬 YT CLIP AI")
            self._update_provider_info("ytclip")
        elif "googleapis" in base_url or "generativelanguage" in base_url:
            self.provider_type_var.set("🆓 Gemini Free Tier")
            self._update_provider_info("gemini")
        elif "openai.com" in base_url:
            self.provider_type_var.set("🤖 OpenAI")
            self._update_provider_info("openai")
        else:
            self.provider_type_var.set("⚙️ CUSTOM")
            self.url_section.pack(fill="x", pady=(0, 10), after=self.content.winfo_children()[1])
            self.provider_info_label.configure(text="")
            self._provider_link_url = ""
        
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, base_url)
        
        self.key_entry.delete(0, "end")
        self.key_entry.insert(0, provider.get("api_key", ""))
        
        saved_model = provider.get("model", "")
        
        # Load model based on input type
        if self.USE_MANUAL_INPUT:
            # Manual input mode
            self.model_entry.delete(0, "end")
            if saved_model:
                self.model_entry.insert(0, saved_model)
            else:
                self.model_entry.insert(0, self.DEFAULT_MODEL)
        else:
            # Dropdown mode
            if saved_model:
                if self.FIXED_MODELS:
                    # For fixed models, just set the value
                    if saved_model in self.FIXED_MODELS:
                        self.model_var.set(saved_model)
                    else:
                        self.model_var.set(self.FIXED_MODELS[0])
                else:
                    # For dynamic models, add to dropdown if not empty
                    self.model_var.set(saved_model)
                    current_values = list(self.model_dropdown.cget("values"))
                    if saved_model not in current_values:
                        self.model_dropdown.configure(values=[saved_model] + current_values)
        
        # Load system message if textbox exists
        if self.system_message_textbox:
            # Try provider-specific system_message first, fallback to root system_prompt
            system_message = provider.get("system_message", "")
            if not system_message:
                system_message = config_dict.get("system_prompt", "")
            self.system_message_textbox.delete("1.0", "end")
            self.system_message_textbox.insert("1.0", system_message)
    
    def save_settings(self):
        """Save settings"""
        api_key = self.key_entry.get().strip()
        
        # Get model from entry or dropdown
        if self.USE_MANUAL_INPUT:
            model = self.model_entry.get().strip()
            if not model:
                model = self.DEFAULT_MODEL
        else:
            model = self.model_var.get().strip()
        
        url = self.get_base_url()
        
        if not api_key:
            messagebox.showerror("Error", "API Key is required")
            return
        
        if not model or model.startswith("--"):
            messagebox.showerror("Error", "Please select a model")
            return
        
        # Handle both ConfigManager and dict
        if hasattr(self.config, 'config'):
            config_dict = self.config.config
        else:
            config_dict = self.config
        
        # Update config
        if "ai_providers" not in config_dict:
            config_dict["ai_providers"] = {}
        
        provider_config = {
            "base_url": url,
            "api_key": api_key,
            "model": model
        }
        
        # Save system message if textbox exists
        if self.system_message_textbox:
            system_message = self.system_message_textbox.get("1.0", "end").strip()
            if system_message:
                provider_config["system_message"] = system_message
        
        config_dict["ai_providers"][self.provider_key] = provider_config
        
        # Call save callback with the full config dict (not just ai_providers)
        if self.on_save_callback:
            self.on_save_callback(config_dict)
        
        messagebox.showinfo("Success", f"{self.title} settings saved!")
        self.on_back()
