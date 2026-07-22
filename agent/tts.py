import os
import ctypes
import edge_tts
import asyncio
import threading

def _generate_and_play_sync(text, filename):
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

        # Create a unique alias for MCI
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
    loop.run_until_complete(_generate_and_play())
    loop.close()

def play_voice_async(text, filename="speech.mp3"):
    """Plays TTS in a background thread."""
    t = threading.Thread(target=_generate_and_play_sync, args=(text, filename))
    t.daemon = True
    t.start()
