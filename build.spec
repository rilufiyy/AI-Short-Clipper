# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for YT Short Clipper Desktop App

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect OpenCV data (haar cascades)
opencv_data = collect_data_files('cv2')

# Collect mediapipe data files
try:
    mediapipe_data = collect_data_files('mediapipe')
except Exception:
    mediapipe_data = []

# Icon path
icon_path = 'assets/icon.ico' if os.path.exists('assets/icon.ico') else None

# Locate yt-dlp.exe dynamically
ytdlp_exe = os.path.join(os.path.dirname(sys.executable), 'Scripts', 'yt-dlp.exe')
if not os.path.exists(ytdlp_exe):
    ytdlp_exe = os.path.join(os.path.dirname(sys.executable), 'yt-dlp.exe')
if not os.path.exists(ytdlp_exe):
    ytdlp_exe = os.path.join('venv', 'Scripts', 'yt-dlp.exe')

# Bundle rclone.exe if present in project folder
extra_binaries = []
if os.path.exists('rclone.exe'):
    extra_binaries.append(('rclone.exe', '.'))
if os.path.exists(ytdlp_exe):
    extra_binaries.append((ytdlp_exe, '.'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=extra_binaries,
    datas=[
        *opencv_data,
        *mediapipe_data,
        ('assets', 'assets'),
        ('clipper_core.py', '.'),
        ('youtube_uploader.py', '.'),
        ('gdrive_uploader.py', '.'),
        ('telegram_notifier.py', '.'),
        ('tiktok_uploader.py', '.'),
        ('version.py', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'darkdetect',
        'openai',
        'cv2',
        'numpy',
        'PIL',
        'PIL._tkinter_finder',
        'PIL.Image',
        'mediapipe',
        'mediapipe.python.solutions.face_detection',
        'mediapipe.python.solutions.face_mesh',
        'curl_cffi',
        'curl_cffi.requests',
        'yt_dlp',
        'google.oauth2.credentials',
        'google.oauth2.service_account',
        'google_auth_oauthlib.flow',
        'googleapiclient.discovery',
        'googleapiclient.http',
        'requests',
        'requests_oauthlib',
        'absl',
        'absl.logging',
        'flatbuffers',
        'sounddevice',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'json',
        'threading',
        'subprocess',
        'pathlib',
        'datetime',
        'base64',
        'struct',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'scipy',
        'pandas',
        'torch',
        'tensorflow',
        'whisper',
        'pytest',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AIShortClipper_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
