"""
Clipping page for video clipping workflow
"""

import customtkinter as ctk
from utils.logger import get_error_log_path


class ClippingPage(ctk.CTkFrame):
    """Clipping page - shows progress during video clipping"""

    def __init__(self, parent, on_cancel_callback, on_back_callback, on_open_output_callback,
                 on_browse_callback, on_save_to_drive_callback=None):
        super().__init__(parent)
        self.on_cancel = on_cancel_callback
        self.on_back = on_back_callback
        self.on_open_output = on_open_output_callback
        self.on_browse = on_browse_callback
        self.on_save_to_drive = on_save_to_drive_callback

        self.create_ui()
    
    def open_github(self):
        """Open GitHub repository"""
        import webbrowser
        webbrowser.open("https://github.com/jipraks/yt-short-clipper")
    
    def open_discord(self):
        """Open Discord server"""
        import webbrowser
        webbrowser.open("https://s.id/ytsdiscord")
    
    def show_page(self, page_name: str):
        """Navigate to another page"""
        pass
    
    def create_ui(self):
        """Create the clipping page UI"""
        from components.page_layout import PageHeader, PageFooter
        
        self.configure(fg_color=("#1a1a1a", "#0a0a0a"))
        
        # Header
        header = PageHeader(self, self, show_nav_buttons=False, show_back_button=True, page_title="✂️ Clipping Videos")
        header.pack(fill="x", padx=20, pady=(15, 10))
        
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Progress section
        progress_frame = ctk.CTkFrame(main, fg_color=("gray90", "gray17"))
        progress_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(progress_frame, text="Clipping Progress", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=15, pady=(12, 8))
        
        # Progress info
        info_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 12))
        
        # Current clip info
        self.current_clip_label = ctk.CTkLabel(info_frame, text="Preparing...", 
            font=ctk.CTkFont(size=14, weight="bold"))
        self.current_clip_label.pack(anchor="w", pady=(0, 5))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(info_frame, height=20)
        self.progress_bar.pack(fill="x", pady=(0, 5))
        self.progress_bar.set(0)
        
        # Progress text (X of Y clips)
        self.progress_text = ctk.CTkLabel(info_frame, text="0 / 0 clips processed", 
            font=ctk.CTkFont(size=11), text_color="gray")
        self.progress_text.pack(anchor="w")
        
        # Current status
        self.status_frame = ctk.CTkFrame(main)
        self.status_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Initializing...", 
            font=ctk.CTkFont(size=12), wraplength=480)
        self.status_label.pack(pady=12)
        
        # Buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        row1 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 5))
        
        self.cancel_btn = ctk.CTkButton(row1, text="❌ Cancel", height=45, fg_color="#c0392b", 
            hover_color="#e74c3c", command=self.on_cancel)
        self.cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.back_btn = ctk.CTkButton(row1, text="← Back", height=45, state="disabled", command=self.on_back)
        self.back_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        row2 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        row2.pack(fill="x")
        
        self.open_btn = ctk.CTkButton(row2, text="📂 Open Output", height=45, state="disabled", command=self.on_open_output)
        self.open_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.results_btn = ctk.CTkButton(row2, text="📂 Browse Sessions", height=45, state="disabled",
            fg_color="#27ae60", hover_color="#2ecc71", command=self.on_browse)
        self.results_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # Row 3 — Save to Drive (hidden until complete)
        self.drive_row = ctk.CTkFrame(btn_frame, fg_color="transparent")
        self.drive_btn = ctk.CTkButton(
            self.drive_row, text="☁️ Save to Drive", height=45,
            fg_color="#1a73e8", hover_color="#1558b0",
            command=self._on_save_to_drive,
        )
        self.drive_btn.pack(fill="x")
        self.drive_status = ctk.CTkLabel(self.drive_row, text="", font=ctk.CTkFont(size=10), text_color="gray")
        self.drive_status.pack()
        
        # Footer
        footer = PageFooter(self, self)
        footer.pack(fill="x", padx=20, pady=(10, 15), side="bottom")
    
    def reset_ui(self):
        """Reset UI for new clipping"""
        self.progress_bar.set(0)
        self.current_clip_label.configure(text="Preparing...")
        self.progress_text.configure(text="0 / 0 clips processed")
        self.status_label.configure(text="Initializing...")
        self.cancel_btn.configure(state="normal")
        self.open_btn.configure(state="disabled")
        self.back_btn.configure(state="disabled")
        self.results_btn.configure(state="disabled")
    
    def update_progress(self, current: int, total: int, clip_title: str = ""):
        """Update progress bar and text"""
        if total > 0:
            progress = current / total
            self.progress_bar.set(progress)
        
        self.progress_text.configure(text=f"{current} / {total} clips processed")
        
        if clip_title:
            self.current_clip_label.configure(text=f"Processing: {clip_title[:50]}")
    
    def update_status(self, msg: str):
        """Update status label"""
        self.status_label.configure(text=msg)
    
    def _on_save_to_drive(self):
        if self.on_save_to_drive:
            self.drive_btn.configure(state="disabled", text="☁️ Uploading...")
            self.drive_status.configure(text="")
            self.on_save_to_drive(self._drive_upload_done)

    def _drive_upload_done(self, success: bool, msg: str = ""):
        if success:
            self.drive_btn.configure(text="☁️ Uploaded ✓", state="disabled", fg_color="#27ae60")
            self.drive_status.configure(text=msg or "Upload selesai", text_color="#27ae60")
        else:
            self.drive_btn.configure(state="normal", text="☁️ Save to Drive")
            self.drive_status.configure(text=msg or "Upload gagal — coba lagi", text_color="red")

    def on_complete(self):
        """Called when clipping completes successfully"""
        self.status_label.configure(text="✅ All clips created successfully!")
        self.cancel_btn.configure(state="disabled")
        self.open_btn.configure(state="normal")
        self.back_btn.configure(state="normal")
        self.results_btn.configure(state="normal")
        self.current_clip_label.configure(text="✓ Complete")
        # Tampilkan tombol Save to Drive kalau callback tersedia
        if self.on_save_to_drive:
            self.drive_row.pack(fill="x", pady=(8, 0))
    
    def on_cancelled(self):
        """Called when clipping is cancelled"""
        self.status_label.configure(text="⚠️ Cancelled by user")
        self.cancel_btn.configure(state="disabled")
        self.back_btn.configure(state="normal")
        self.current_clip_label.configure(text="⚠ Cancelled")
    
    def on_error(self, error: str):
        """Called when clipping encounters an error"""
        error_log = get_error_log_path()
        
        if error_log:
            error_msg = f"❌ {error}\n\n📄 Error details saved to:\n{error_log}"
        else:
            error_msg = f"❌ {error}"
        
        self.status_label.configure(text=error_msg)
        self.cancel_btn.configure(state="disabled")
        self.back_btn.configure(state="normal")
        self.current_clip_label.configure(text="✗ Failed")
