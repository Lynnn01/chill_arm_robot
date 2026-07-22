"""
modules/tts/domain/speech.py
Domain Layer: Value Objects for Speech Messages
"""

class SpeechMessage:
    """Value Object representing a speech text message to synthesize."""
    def __init__(self, text: str, voice_name: str = "th-TH-NiwatNeural"):
        if not text or not text.strip():
            raise ValueError("SpeechMessage text cannot be empty.")
        self._text = text.strip()
        self._voice_name = voice_name

    @property
    def text(self) -> str:
        return self._text

    @property
    def voice_name(self) -> str:
        return self._voice_name

    def __repr__(self) -> str:
        return f"SpeechMessage(text='{self._text[:20]}...')"
