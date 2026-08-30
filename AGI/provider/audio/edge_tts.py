# AGI Provider - Audio / Edge TTS
# Microsoft Edge Text-to-Speech প্রোভাইডার

import edge_tts
import asyncio

class EdgeTTSProvider:
    """Microsoft Edge TTS ব্যবহার করে অডিও জেনারেট করার প্রোভাইডার"""
    
    @staticmethod
    async def text_to_speech(text: str, voice: str = "en-US-JennyNeural"):
        """টেক্সট থেকে অডিও তৈরি করে"""
        tts = edge_tts.Communicate(text, voice)
        audio_data = b""
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    
    @staticmethod
    def get_voices():
        """সব উপলব্ধ ভয়েসের লিস্ট"""
        return asyncio.run(edge_tts.list_voices())