"""
Telegram Notification Settings Sub-Page
"""

import threading
import webbrowser
import customtkinter as ctk
from tkinter import messagebox

from pages.settings.base_dialog import BaseSettingsSubPage


class TelegramSettingsSubPage(BaseSettingsSubPage):
    """Sub-page for configuring Telegram bot notifications"""

    def __init__(self, parent, config, on_save_callback, on_back_callback):
        self.config = config
        self.on_save_callback = on_save_callback

        super().__init__(parent, "Telegram Notifications", on_back_callback)

        self.create_content()
        self.load_config()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def create_content(self):
        # ── Info card ──────────────────────────────────────────────────
        info_card = ctk.CTkFrame(self.content, fg_color=("#e3f2fd", "#0d2137"), corner_radius=10)
        info_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(info_card, text="📱 Notifikasi Telegram",
            font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(info_card,
            text=(
                "Setiap kali proses clip selesai, kamu akan dapat notifikasi langsung\n"
                "ke Telegram — termasuk judul clip, virality score, dan status Drive upload.\n\n"
                "Credentials disimpan di config.json di mesin kamu saja.\n"
                "TIDAK pernah embed di EXE."
            ),
            font=ctk.CTkFont(size=10), text_color="gray",
            justify="left", wraplength=500).pack(anchor="w", padx=15, pady=(0, 12))

        # ── Enable toggle ──────────────────────────────────────────────
        toggle_section = self.create_section("Status")
        toggle_frame = ctk.CTkFrame(toggle_section, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(toggle_frame, text="Aktifkan notifikasi Telegram",
            font=ctk.CTkFont(size=11)).pack(side="left")

        self.enabled_var = ctk.BooleanVar(value=False)
        self.enabled_switch = ctk.CTkSwitch(toggle_frame, text="",
            variable=self.enabled_var, width=46, height=24,
            command=self._on_toggle)
        self.enabled_switch.pack(side="right")

        # ── Bot Token ──────────────────────────────────────────────────
        token_section = self.create_section("Bot Token")
        token_frame = ctk.CTkFrame(token_section, fg_color="transparent")
        token_frame.pack(fill="x", padx=15, pady=(0, 12))

        header_row = ctk.CTkFrame(token_frame, fg_color="transparent")
        header_row.pack(fill="x")

        ctk.CTkLabel(header_row, text="Bot Token",
            font=ctk.CTkFont(size=11)).pack(side="left")

        botfather_link = ctk.CTkLabel(header_row,
            text="Buat bot di @BotFather →",
            font=ctk.CTkFont(size=9), text_color=("#3B8ED0", "#5B9ED0"), cursor="hand2")
        botfather_link.pack(side="right")
        botfather_link.bind("<Button-1>",
            lambda e: webbrowser.open("https://t.me/BotFather"))

        ctk.CTkLabel(token_frame,
            text="Format: 1234567890:AAH... (dari BotFather setelah /newbot)",
            font=ctk.CTkFont(size=9), text_color="gray").pack(anchor="w", pady=(2, 5))

        self.token_entry = ctk.CTkEntry(token_frame,
            placeholder_text="1234567890:AAH...",
            show="•", height=36)
        self.token_entry.pack(fill="x")

        # Show/hide toggle for token
        show_token_btn = ctk.CTkButton(token_frame, text="👁 Tampilkan",
            height=28, width=110,
            fg_color=("gray70", "gray30"), hover_color=("gray60", "gray40"),
            font=ctk.CTkFont(size=10),
            command=lambda: self._toggle_show(self.token_entry, show_token_btn, "Token"))
        show_token_btn.pack(anchor="e", pady=(4, 0))

        # ── Chat ID ────────────────────────────────────────────────────
        chatid_section = self.create_section("Chat ID")
        chatid_frame = ctk.CTkFrame(chatid_section, fg_color="transparent")
        chatid_frame.pack(fill="x", padx=15, pady=(0, 12))

        ctk.CTkLabel(chatid_frame, text="Chat ID",
            font=ctk.CTkFont(size=11)).pack(anchor="w")
        ctk.CTkLabel(chatid_frame,
            text=(
                "Masukkan token dulu, lalu kirim pesan ke bot kamu, "
                "lalu klik 'Ambil Chat ID'."
            ),
            font=ctk.CTkFont(size=9), text_color="gray",
            wraplength=480, justify="left").pack(anchor="w", pady=(2, 5))

        chatid_row = ctk.CTkFrame(chatid_frame, fg_color="transparent")
        chatid_row.pack(fill="x")

        self.chatid_entry = ctk.CTkEntry(chatid_row,
            placeholder_text="contoh: 123456789 atau -100123456789 (grup)",
            height=36)
        self.chatid_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.fetch_btn = ctk.CTkButton(chatid_row, text="Ambil Chat ID",
            width=120, height=36,
            fg_color=("#3B8ED0", "#1F6AA5"),
            hover_color=("#36719F", "#144870"),
            command=self._fetch_chat_id)
        self.fetch_btn.pack(side="right")

        # Chat ID results list (shown after fetch)
        self.chatid_results_frame = ctk.CTkFrame(chatid_frame, fg_color="transparent")

        # ── Test & Save ────────────────────────────────────────────────
        actions_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(10, 0))

        self.test_btn = ctk.CTkButton(actions_frame, text="📨 Kirim Pesan Test",
            height=40,
            fg_color=("#27ae60", "#1e8449"),
            hover_color=("#229954", "#196f3d"),
            command=self._send_test)
        self.test_btn.pack(fill="x", pady=(0, 8))

        self.create_save_button(self.save_settings)

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _on_toggle(self):
        """Visual feedback when toggle changes."""
        state = self.enabled_var.get()
        self.enabled_switch.configure(text="ON" if state else "")

    def _toggle_show(self, entry: ctk.CTkEntry, btn: ctk.CTkButton, label: str):
        """Toggle show/hide for a password-style entry."""
        if entry.cget("show") == "•":
            entry.configure(show="")
            btn.configure(text=f"🙈 Sembunyikan")
        else:
            entry.configure(show="•")
            btn.configure(text=f"👁 Tampilkan")

    def _fetch_chat_id(self):
        """Call getUpdates and show chat_id choices."""
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("Error", "Masukkan Bot Token dulu.")
            return

        self.fetch_btn.configure(state="disabled", text="Mengambil...")

        def do_fetch():
            try:
                from telegram_notifier import get_recent_chat_ids
                chats = get_recent_chat_ids(token)
                self.after(0, lambda: self._show_chat_options(chats))
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._fetch_error(err))

        threading.Thread(target=do_fetch, daemon=True).start()

    def _show_chat_options(self, chats: list):
        self.fetch_btn.configure(state="normal", text="Ambil Chat ID")

        # Clear previous results
        for w in self.chatid_results_frame.winfo_children():
            w.destroy()

        if not chats:
            messagebox.showinfo(
                "Tidak Ada Pesan",
                "Bot belum menerima pesan.\n\n"
                "Langkah:\n"
                "1. Buka Telegram\n"
                "2. Cari bot kamu dan klik 'Start' atau kirim pesan apa saja\n"
                "3. Klik 'Ambil Chat ID' lagi"
            )
            return

        self.chatid_results_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(self.chatid_results_frame,
            text="Pilih chat yang ingin menerima notifikasi:",
            font=ctk.CTkFont(size=10), text_color="gray").pack(anchor="w", pady=(0, 5))

        for chat in chats:
            cid = chat["chat_id"]
            name = chat["name"]
            ctype = chat.get("type", "")
            label = f"{name}  ({ctype}, ID: {cid})"

            btn = ctk.CTkButton(self.chatid_results_frame, text=label,
                height=32, anchor="w",
                fg_color=("gray80", "gray25"),
                hover_color=("gray70", "gray30"),
                text_color=("black", "white"),
                font=ctk.CTkFont(size=10),
                command=lambda c=cid: self._select_chat_id(c))
            btn.pack(fill="x", pady=2)

    def _select_chat_id(self, chat_id: str):
        self.chatid_entry.delete(0, "end")
        self.chatid_entry.insert(0, chat_id)

    def _fetch_error(self, error: str):
        self.fetch_btn.configure(state="normal", text="Ambil Chat ID")
        messagebox.showerror("Gagal", f"Tidak bisa mengambil update:\n\n{error}")

    def _send_test(self):
        token = self.token_entry.get().strip()
        chat_id = self.chatid_entry.get().strip()

        if not token or not chat_id:
            messagebox.showerror("Error", "Isi Bot Token dan Chat ID dulu.")
            return

        self.test_btn.configure(state="disabled", text="Mengirim...")

        def do_test():
            try:
                from telegram_notifier import send_message
                send_message(token, chat_id,
                    "✅ <b>Test notifikasi YT Short Clipper berhasil!</b>\n\n"
                    "Kamu akan menerima notifikasi seperti ini setiap kali "
                    "proses clip selesai.")
                self.after(0, self._test_success)
            except Exception as e:
                err = str(e)
                self.after(0, lambda: self._test_error(err))

        threading.Thread(target=do_test, daemon=True).start()

    def _test_success(self):
        self.test_btn.configure(state="normal", text="📨 Kirim Pesan Test")
        messagebox.showinfo("Berhasil", "Pesan test berhasil dikirim ke Telegram!")

    def _test_error(self, error: str):
        self.test_btn.configure(state="normal", text="📨 Kirim Pesan Test")
        messagebox.showerror("Gagal", f"Gagal mengirim pesan test:\n\n{error}")

    # ------------------------------------------------------------------
    # Config load/save
    # ------------------------------------------------------------------

    def load_config(self):
        cfg = self.config.config if hasattr(self.config, 'config') else self.config
        tg = cfg.get("telegram", {})

        self.enabled_var.set(tg.get("enabled", False))
        self._on_toggle()

        token = tg.get("bot_token", "")
        if token:
            self.token_entry.delete(0, "end")
            self.token_entry.insert(0, token)

        chat_id = tg.get("chat_id", "")
        if chat_id:
            self.chatid_entry.delete(0, "end")
            self.chatid_entry.insert(0, chat_id)

    def save_settings(self):
        token = self.token_entry.get().strip()
        chat_id = self.chatid_entry.get().strip()
        enabled = self.enabled_var.get()

        if enabled and (not token or not chat_id):
            messagebox.showerror("Error",
                "Untuk mengaktifkan notifikasi, isi Bot Token dan Chat ID dulu.")
            return

        cfg = self.config.config if hasattr(self.config, 'config') else self.config
        cfg["telegram"] = {
            "enabled": enabled,
            "bot_token": token,
            "chat_id": chat_id,
        }

        if self.on_save_callback:
            self.on_save_callback(cfg)

        messagebox.showinfo("Tersimpan",
            "Pengaturan Telegram disimpan!"
            + ("\n\nNotifikasi AKTIF ✅" if enabled else "\n\nNotifikasi nonaktif."))
        self.on_back()

    # Footer compatibility
    def show_page(self, page_name): pass
    def open_github(self): webbrowser.open("https://github.com/jipraks/yt-short-clipper")
    def open_discord(self): webbrowser.open("https://s.id/ytsdiscord")