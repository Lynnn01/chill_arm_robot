"""
modules/tts/application/ports.py
Application Layer: Ports (Interfaces) for Text-to-Speech Services
"""

from typing import Protocol
from modules.tts.domain.speech import SpeechMessage

class TTSServicePort(Protocol):
    """Hexagonal Port Interface for Speech Synthesis and Audio Playback."""
    
    def play_voice_async(self, message: SpeechMessage, filename: str = "speech.mp3") -> None:
        ...
