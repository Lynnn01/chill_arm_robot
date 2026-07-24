"""
agent/tts.py — Legacy compatibility wrapper delegating to Unified Architecture modules.tts
"""

import os
import ctypes
import asyncio
import threading
import edge_tts
_audio_lock = threading.Lock()

def play_voice_async(text: str, filename: str = "speech.mp3") -> None:
    """Plays TTS in a background thread."""
    if not text or not text.strip():
        return
        
    import armconfig
    if not getattr(armconfig, 'SPEAKER_ON', False):
        return

    t = threading.Thread(target=_generate_and_play_sync, args=(text.strip(), filename))
    t.daemon = True
    t.start()


def _generate_and_play_sync(text: str, filename: str):
    async def _generate_and_play():
        try:
            from hardware import init

            sounds_dir = os.path.join(init.PROJECT_ROOT, "sounds")
        except ImportError:
            sounds_dir = os.path.join(os.getcwd(), "sounds")

        os.makedirs(sounds_dir, exist_ok=True)
        base_name = os.path.basename(filename)
        mp3_path = os.path.join(sounds_dir, base_name)

        try:
            communicate = edge_tts.Communicate(text, "th-TH-NiwatNeural")
            await communicate.save(mp3_path)
        except Exception as e:
            print(f"⚠️ <SYSTEM>: Edge TTS Error: {e}")
            return

        alias = (
            base_name.replace(".wav", "")
            .replace(".mp3", "")
            .replace("_", "")
            .replace("-", "")
        )

        with _audio_lock:
            try:
                if os.name == 'nt':
                    # Windows playback via MCI
                    ctypes.windll.winmm.mciSendStringW('close all', None, 0, None)
                    device_type = "waveaudio" if mp3_path.endswith(".wav") else "mpegvideo"
                    ctypes.windll.winmm.mciSendStringW(f'open "{mp3_path}" type {device_type} alias {alias}', None, 0, None)
                    ctypes.windll.winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
                    ctypes.windll.winmm.mciSendStringW(f'close {alias}', None, 0, None)
                else:
                    # Linux/Jetson playback via standard CLI players (Only use pure CLI players to avoid X11 crashes with Tkinter)
                    import subprocess
                    players = [
                        ["mpg123", "-q", mp3_path]
                    ]
                    played = False
                    for cmd in players:
                        try:
                            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            if result.returncode == 0:
                                played = True
                                break
                        except FileNotFoundError:
                            continue
                    
                    if not played:
                        print("⚠️ <SYSTEM>: ไม่มีโปรแกรมเล่นเสียงติดตั้งอยู่ (Please run: sudo apt install mpg123)")
            except Exception as e:
                print(f"⚠️ <SYSTEM>: Playback Error: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_generate_and_play())
    finally:
        loop.close()
