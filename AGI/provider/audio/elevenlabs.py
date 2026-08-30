from __future__ import annotations

import os
import asyncio
import aiohttp
import json

try:
    import elevenlabs
    from elevenlabs import generate, play, Voice, VoiceSettings
    has_elevenlabs = True
except ImportError:
    has_elevenlabs = False

from ...typing import AsyncResult, Messages
from ...providers.response import AudioResponse
from ...image.copy_images import get_filename, get_media_dir, ensure_media_dir
from ..base_provider import AsyncGeneratorProvider, ProviderModelMixin
from ..helper import get_last_message


class ElevenLabs(AsyncGeneratorProvider, ProviderModelMixin):
    label = "ElevenLabs"
    working = has_elevenlabs
    model_id = "eleven_monolingual_v1"
    default_language = "en"
    default_format = "mp3"
    
    # ElevenLabs API endpoint
    API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    
    @classmethod
    def get_models(cls) -> list[str]:
        """ElevenLabs-এর উপলব্ধ মডেলের লিস্ট"""
        return [
            "eleven_monolingual_v1",
            "eleven_multilingual_v1",
            "eleven_turbo_v2",
            "eleven_turbo_v2_5"
        ]
    
    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        prompt: str = None,
        audio: dict = {},
        api_key: str = None,
        **kwargs,
    ) -> AsyncResult:
        """
        ElevenLabs API ব্যবহার করে টেক্সট থেকে অডিও জেনারেট করে
        
        Args:
            model: মডেলের নাম
            messages: মেসেজের লিস্ট
            proxy: প্রক্সি সেটিংস
            prompt: টেক্সট প্রম্পট
            audio: অডিও প্যারামিটার (voice, format, speed, stability, similarity_boost)
            api_key: ElevenLabs API কী
        """
        prompt = get_last_message(messages, prompt)
        if not prompt:
            raise ValueError("Prompt is empty.")
            
        if not api_key:
            raise ValueError("ElevenLabs API key is required. Please provide api_key parameter.")
        
        # অডিও প্যারামিটার সেট করা
        voice = audio.get("voice", "21m00Tcm4TlvDq8ikWAM")  # ডিফল্ট ভয়েস (Rachel)
        format = audio.get("format", cls.default_format)
        speed = audio.get("speed", 1.0)
        stability = audio.get("stability", 0.5)
        similarity_boost = audio.get("similarity_boost", 0.75)
        
        filename = get_filename([cls.model_id], prompt, f".{format}", prompt)
        target_path = os.path.join(get_media_dir(), filename)
        ensure_media_dir()
        
        # API রিকোয়েস্ট তৈরি
        url = f"{cls.API_URL}/{voice}"
        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": prompt,
            "model_id": model if model else cls.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "speed": speed
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data, proxy=proxy) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"ElevenLabs API error: {response.status} - {error_text}")
                
                # অডিও ফাইল সেভ করা
                audio_data = await response.read()
                with open(target_path, "wb") as f:
                    f.write(audio_data)
        
        yield AudioResponse(f"/media/{filename}", voice=voice, text=prompt)
    
    @classmethod
    async def get_voices(cls, api_key: str = None):
        """ElevenLabs-এর উপলব্ধ ভয়েসের লিস্ট"""
        if not api_key:
            raise ValueError("API key required")
            
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("voices", [])
                else:
                    error_text = await response.text()
                    raise Exception(f"Error fetching voices: {response.status} - {error_text}")