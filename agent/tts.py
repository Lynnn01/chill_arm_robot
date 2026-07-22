"""
agent/tts.py — Legacy compatibility wrapper delegating to Unified Architecture modules.tts
"""

from modules.tts.domain.speech import SpeechMessage
from modules.tts.infrastructure.edge_tts_adapter import EdgeTTSAdapter

_tts_adapter = EdgeTTSAdapter()

def play_voice_async(text: str, filename: str = "speech.mp3") -> None:
    """Plays TTS in a background thread using the unified EdgeTTSAdapter."""
    message = SpeechMessage(text=text)
    _tts_adapter.play_voice_async(message, filename=filename)

