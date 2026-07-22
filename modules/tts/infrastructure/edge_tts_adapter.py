r"""
modules/tts/infrastructure/edge_tts_adapter.py
Infrastructure Layer: Concrete Adapter for Edge TTS & MCI Windows Audio Player
Saves generated audio files directly to R:\chill_arm_robot\sounds\
"""

import os
import ctypes
import asyncio
import threading
import edge_tts
from modules.tts.domain.speech import SpeechMessage
from modules.tts.application.ports import TTSServicePort

class EdgeTTSAdapter(TTSServicePort):
    """Adapter implementing TTSServicePort using Microsoft Edge TTS and Windows MCI."""

    def __init__(self, sounds_dir: str = None):
        if not sounds_dir:
            try:
                from hardware import init
                self._sounds_dir = os.path.join(init.PROJECT_ROOT, "sounds")
            except ImportError:
                self._sounds_dir = os.path.join(os.getcwd(), "sounds")
        else:
            self._sounds_dir = sounds_dir

        os.makedirs(self._sounds_dir, exist_ok=True)

    def play_voice_async(self, message: SpeechMessage, filename: str = "speech.mp3") -> None:
        t = threading.Thread(target=self._generate_and_play_sync, args=(message.text, message.voice_name, filename))
        t.daemon = True
        t.start()

    def _generate_and_play_sync(self, text: str, voice_name: str, filename: str):
        async def _generate_and_play():
            base_name = os.path.basename(filename)
            mp3_path = os.path.join(self._sounds_dir, base_name)

            try:
                communicate = edge_tts.Communicate(text, voice_name)
                await communicate.save(mp3_path)
            except Exception as e:
                print(f"⚠️ <SYSTEM>: Edge TTS Error: {e}")
                return

            alias = base_name.replace(".wav", "").replace(".mp3", "").replace("_", "").replace("-", "")
            
            try:
                ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                device_type = "waveaudio" if mp3_path.endswith(".wav") else "mpegvideo"
                ctypes.windll.winmm.mciSendStringW(f'open "{mp3_path}" type {device_type} alias {alias}', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
                ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
            except Exception as e:
                print(f"⚠️ <SYSTEM>: Playback Error: {e}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_generate_and_play())
        finally:
            loop.close()
