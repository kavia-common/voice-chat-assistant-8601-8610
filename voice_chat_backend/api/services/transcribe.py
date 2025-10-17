"""Transcription service with OpenAI-first strategy and SpeechRecognition fallback.

This module intentionally avoids system-level dependencies like pyaudio/ffmpeg.
It operates on WAV/MP3 inputs as accepted by the API (validated in serializers).
"""

from typing import Tuple

from django.conf import settings

# Try OpenAI SDK >=1.x
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

# Try SpeechRecognition for local fallback (no PyAudio required for file-based recognition)
try:
    import speech_recognition as sr  # type: ignore
except Exception:
    sr = None  # type: ignore


def _openai_client():
    api_key = getattr(settings, "OPENAI_API_KEY", "").strip()
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def _transcribe_with_openai(file_path: str) -> Tuple[bool, str]:
    """Attempt to transcribe using OpenAI Whisper (server-side)."""
    client = _openai_client()
    if client is None:
        return False, "OpenAI is not configured."
    model = getattr(settings, "OPENAI_TRANSCRIPTION_MODEL", "whisper-1")
    try:
        # openai>=1.x audio transcription
        with open(file_path, "rb") as f:
            resp = client.audio.transcriptions.create(
                model=model,
                file=f,
            )
        # Attempt to extract text across SDK variants
        text = getattr(resp, "text", "") or getattr(resp, "data", None)
        if isinstance(text, dict):
            text = text.get("text", "")
        if not text and hasattr(resp, "to_dict"):
            text = resp.to_dict().get("text", "")
        if not text:
            # Some SDK responses may nest under 'text'
            text = str(resp)
        return True, str(text).strip()
    except Exception as ex:
        return False, f"OpenAI transcription failed: {ex}"


def _transcribe_with_speech_recognition(file_path: str) -> Tuple[bool, str]:
    """Fallback transcription using SpeechRecognition recognizer with Sphinx if available.

    Uses file-based recognition to avoid requiring microphone (PyAudio).
    Note: Accuracy depends on audio format/quality and installed engines.
    """
    if sr is None:
        return False, "SpeechRecognition is not available."

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
    except Exception as ex:
        return False, f"Could not read audio file: {ex}"

    # Try Sphinx (offline) if pocketphinx is available
    try:
        return True, recognizer.recognize_sphinx(audio)  # type: ignore[attr-defined]
    except Exception:
        pass

    # Try Google Web Speech API (may fail without internet, but doesn't require API keys)
    try:
        return True, recognizer.recognize_google(audio)
    except Exception as ex:
        return False, f"SpeechRecognition failed: {ex}"


# PUBLIC_INTERFACE
def transcribe_audio(file_path: str) -> Tuple[bool, str]:
    """Transcribe an audio file.

    Preference:
    1) OpenAI if OPENAI_API_KEY is configured.
    2) Fallback to SpeechRecognition.

    Returns:
        (ok, result) where result is transcript or error message.
    """
    # Try OpenAI first if configured
    if getattr(settings, "OPENAI_API_KEY", "").strip():
        ok, text = _transcribe_with_openai(file_path)
        if ok:
            return True, text

    # Fallback to SpeechRecognition
    ok, text = _transcribe_with_speech_recognition(file_path)
    if ok:
        return True, text

    # If both failed, return a consolidated error
    return False, text or "Transcription failed."
