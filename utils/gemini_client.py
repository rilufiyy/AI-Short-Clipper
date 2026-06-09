"""
Gemini Native API Client
Handles STT (transcription) and TTS via Google Gemini API (non-OpenAI-compatible endpoints).
Uses only urllib — no extra dependencies.
"""

import base64
import json
import os
import struct
import urllib.request
import urllib.error

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
GEMINI_UPLOAD_BASE = "https://generativelanguage.googleapis.com/upload/v1beta"

# Gemini TTS voices (mapped from OpenAI voice names for compatibility)
VOICE_MAP = {
    "nova":   "Kore",
    "alloy":  "Aoede",
    "echo":   "Charon",
    "fable":  "Fenrir",
    "onyx":   "Orus",
    "shimmer":"Leda",
}
DEFAULT_TTS_MODEL = "gemini-3.1-flash-tts-preview"
DEFAULT_STT_MODEL = "gemini-2.5-flash"


def detect_provider(api_key: str) -> str:
    """Detect provider from API key format. Returns 'gemini', 'openai', or 'unknown'.

    Known formats:
      Gemini (Google AI Studio): AIza...
      OpenAI: sk-...
      YTClip: ytc-...
    """
    key = api_key.strip()
    # OpenAI-family — very distinctive prefix
    if key.startswith("sk-") or key.startswith("ytc-"):
        return "openai"
    # Google AI Studio keys — older format (AIza) and newer format (AQ.)
    if key.startswith("AIza") or key.startswith("AQ."):
        return "gemini"
    # Unknown — caller should ask user to pick manually
    return "unknown"


def get_provider_configs(api_key: str) -> dict:
    """
    Return ai_providers config for all 4 steps based on detected provider.
    Gemini key → full Gemini config (STT + TTS via native endpoints).
    OpenAI key → full OpenAI config.
    """
    provider = detect_provider(api_key)
    if provider == "gemini":
        return {
            "highlight_finder": {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "api_key": api_key,
                "model": "gemini-2.5-flash",
            },
            "youtube_title_maker": {
                "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
                "api_key": api_key,
                "model": "gemini-2.5-flash",
            },
            "caption_maker": {
                "base_url": GEMINI_API_BASE,
                "api_key": api_key,
                "model": DEFAULT_STT_MODEL,
            },
            "hook_maker": {
                "base_url": GEMINI_API_BASE,
                "api_key": api_key,
                "model": DEFAULT_TTS_MODEL,
            },
        }
    else:  # openai / unknown
        return {
            "highlight_finder": {
                "base_url": "https://api.openai.com/v1",
                "api_key": api_key,
                "model": "gpt-4.1",
            },
            "youtube_title_maker": {
                "base_url": "https://api.openai.com/v1",
                "api_key": api_key,
                "model": "gpt-4.1",
            },
            "caption_maker": {
                "base_url": "https://api.openai.com/v1",
                "api_key": api_key,
                "model": "whisper-1",
            },
            "hook_maker": {
                "base_url": "https://api.openai.com/v1",
                "api_key": api_key,
                "model": "tts-1",
            },
        }


def is_gemini_native(base_url: str) -> bool:
    """True if base_url is a Gemini native endpoint (not the OpenAI-compatible one)."""
    url = (base_url or "").rstrip("/")
    return "googleapis" in url and not url.endswith("openai")


# ─────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────

def _post(api_key: str, endpoint: str, payload: dict, timeout: int = 300) -> dict:
    url = f"{GEMINI_API_BASE}/{endpoint}?key={api_key}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        raise Exception(f"Gemini API error {e.code}: {body[:500]}")


def _upload_file(api_key: str, file_path: str, mime_type: str) -> str:
    """Upload file to Gemini File API (resumable). Returns file URI."""
    file_size = os.path.getsize(file_path)
    display_name = os.path.basename(file_path)

    # Step 1: Initiate resumable upload
    init_url = f"{GEMINI_UPLOAD_BASE}/files?key={api_key}"
    meta = json.dumps({"file": {"display_name": display_name}}).encode("utf-8")
    req = urllib.request.Request(
        init_url, data=meta,
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json",
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        upload_url = resp.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise Exception("Gemini File API: failed to get upload URL")

    # Step 2: Upload bytes
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    req2 = urllib.request.Request(
        upload_url, data=file_bytes,
        headers={
            "Content-Length": str(file_size),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        },
        method="POST"
    )
    with urllib.request.urlopen(req2, timeout=300) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["file"]["uri"]


def _extract_json(text: str) -> dict:
    """Strip markdown code fences and parse JSON from Gemini response."""
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```", 2)
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
        if "```" in text:
            text = text.rsplit("```", 1)[0]
    return json.loads(text.strip())


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = 24000, channels: int = 1, bits: int = 16) -> bytes:
    """Wrap raw PCM bytes in a WAV container."""
    data_size = len(pcm_data)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16, 1, channels, sample_rate,
        sample_rate * channels * bits // 8,
        channels * bits // 8, bits,
        b"data", data_size,
    )
    return header + pcm_data


# ─────────────────────────────────────────
# Public API
# ─────────────────────────────────────────

def transcribe_audio(
    api_key: str,
    audio_path: str,
    language: str = "id",
    model: str = DEFAULT_STT_MODEL,
) -> tuple:
    """
    Transcribe audio using Gemini multimodal.
    Returns (segments, words) where:
      segments: list[{"start": float, "end": float, "text": str}]
      words:    list[{"start": float, "end": float, "word": str}]
    """
    ext = audio_path.lower().rsplit(".", 1)[-1]
    mime_map = {
        "mp3": "audio/mpeg", "mp4": "audio/mp4",
        "wav": "audio/wav", "m4a": "audio/mp4",
        "webm": "audio/webm", "ogg": "audio/ogg",
    }
    mime_type = mime_map.get(ext, "audio/mpeg")
    file_size = os.path.getsize(audio_path)

    # Use File API for files > 15 MB, inline for smaller
    if file_size > 15 * 1024 * 1024:
        file_uri = _upload_file(api_key, audio_path, mime_type)
        audio_part = {"file_data": {"file_uri": file_uri, "mime_type": mime_type}}
    else:
        with open(audio_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")
        audio_part = {"inline_data": {"mime_type": mime_type, "data": audio_b64}}

    lang_hint = f"Language: {language}. " if language and language != "none" else ""
    prompt = (
        f"{lang_hint}Transcribe this audio accurately with timestamps. "
        "Return ONLY valid JSON in this exact format, no extra text: "
        '{"segments": [{"start": 0.0, "end": 2.5, "text": "..."}], '
        '"words": [{"start": 0.0, "end": 0.5, "word": "..."}]}'
    )

    payload = {
        "contents": [{"parts": [audio_part, {"text": prompt}]}],
        "generationConfig": {"temperature": 0},
    }

    resp = _post(api_key, f"models/{model}:generateContent", payload, timeout=300)
    raw_text = resp["candidates"][0]["content"]["parts"][0]["text"]

    try:
        data = _extract_json(raw_text)
    except Exception:
        # Fallback: return the raw text as a single segment
        return [{"start": 0.0, "end": 0.0, "text": raw_text.strip()}], []

    segments = data.get("segments", [])
    words = data.get("words", [])
    return segments, words


def text_to_speech(
    api_key: str,
    text: str,
    voice: str = "nova",
    model: str = DEFAULT_TTS_MODEL,
) -> bytes:
    """
    Generate speech using Gemini TTS.
    Returns WAV bytes (24kHz mono 16-bit PCM).
    voice: OpenAI voice name (nova, alloy, echo, fable, onyx, shimmer) — auto-mapped to Gemini.
    """
    gemini_voice = VOICE_MAP.get(voice.lower(), "Kore")

    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "response_modalities": ["AUDIO"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": gemini_voice}
                }
            },
        },
    }

    resp = _post(api_key, f"models/{model}:generateContent", payload, timeout=120)
    audio_b64 = resp["candidates"][0]["content"]["parts"][0]["inline_data"]["data"]
    pcm_bytes = base64.b64decode(audio_b64)
    return _pcm_to_wav(pcm_bytes, sample_rate=24000)