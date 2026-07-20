import os
import ctypes
import edge_tts
from loguru import logger
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from pipecat.frames.frames import TextFrame

class EdgeTTSProcessor(FrameProcessor):
    """
    A custom Pipecat processor that intercepts TextFrames, generates MP3 using edge-tts, 
    and plays it using Windows winmm API.
    """
    def __init__(self, voice="th-TH-NiwatNeural"):
        super().__init__()
        self.voice = voice

    async def process_frame(self, frame, direction=FrameDirection.DOWNSTREAM):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TextFrame):
            logger.debug(f"EdgeTTSProcessor generating voice for: {frame.text}")
            await self._play_voice(frame.text)
            
        # Push the frame downstream so the pipeline continues normally
        await self.push_frame(frame, direction)

    async def _play_voice(self, text: str):
        try:
            # We must import inside the function to avoid circular imports 
            from hardware import init
            mp3_path = os.path.join(init.PROJECT_ROOT, "speech.mp3")
        except ImportError:
            # Fallback path if hardware.init isn't available
            mp3_path = os.path.join(os.getcwd(), "speech.mp3")
        
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(mp3_path)
            
            # Use winmm.dll of Windows to play MP3
            ctypes.windll.winmm.mciSendStringW('close mymp3', None, 0, None)
            ctypes.windll.winmm.mciSendStringW(f'open "{mp3_path}" type mpegvideo alias mymp3', None, 0, None)
            ctypes.windll.winmm.mciSendStringW('play mymp3 wait', None, 0, None)
            ctypes.windll.winmm.mciSendStringW('close mymp3', None, 0, None)
        except Exception as e:
            logger.error(f"Voice TTS Error: {e}")
