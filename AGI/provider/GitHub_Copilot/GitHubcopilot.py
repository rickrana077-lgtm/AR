from __future__ import annotations

import json
import aiohttp
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any

from ...typing import AsyncResult, Messages
from ..base_provider import AsyncGeneratorProvider, ProviderModelMixin
from ..helper import get_last_message
from .copilotTokenProvider import CopilotTokenProvider
from .sharedTokenManager import SharedTokenManager


class GitHubCopilot(AsyncGeneratorProvider, ProviderModelMixin):
    """
    GitHub Copilot API প্রোভাইডার
    কোড কমপ্লিশন ও চ্যাট রেসপন্স জেনারেট করে
    """
    
    label = "GitHub Copilot"
    url = "https://github.com/copilot"
    working = True
    
    default_model = "copilot"
    models = ["copilot", "copilot-chat"]
    
    # API এন্ডপয়েন্ট
    API_ENDPOINT = "https://api.github.com/copilot_internal/v2"
    CHAT_ENDPOINT = f"{API_ENDPOINT}/chat"
    COMPLETION_ENDPOINT = f"{API_ENDPOINT}/completions"
    
    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        prompt: str = None,
        api_key: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Copilot API ব্যবহার করে রেসপন্স জেনারেট করে
        """
        prompt = get_last_message(messages, prompt)
        if not prompt:
            raise ValueError("Prompt is empty.")
        
        # টোকেন প্রোভাইডার থেকে অ্যাক্সেস টোকেন নিন
        token_provider = CopilotTokenProvider()
        access_token = await token_provider.get_access_token(api_key)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "GitHubCopilot/1.0"
        }
        
        data = {
            "model": model if model else cls.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                cls.CHAT_ENDPOINT,
                headers=headers,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Copilot API error: {response.status} - {error_text}")
                
                if stream:
                    async for line in response.content:
                        if line:
                            line = line.decode('utf-8').strip()
                            if line.startswith("data: "):
                                line = line[6:]
                                if line != "[DONE]":
                                    try:
                                        json_data = json.loads(line)
                                        content = json_data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if content:
                                            yield content
                                    except json.JSONDecodeError:
                                        pass
                else:
                    json_data = await response.json()
                    content = json_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    yield content
    
    @classmethod
    async def get_completion(
        cls,
        prompt: str,
        api_key: str = None,
        **kwargs
    ) -> str:
        """
        শুধু কোড কমপ্লিশন (ChatGPT নয়)
        """
        token_provider = CopilotTokenProvider()
        access_token = await token_provider.get_access_token(api_key)
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "prompt": prompt,
            "max_tokens": kwargs.get("max_tokens", 100),
            "temperature": kwargs.get("temperature", 0.7)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                cls.COMPLETION_ENDPOINT,
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    json_data = await response.json()
                    return json_data.get("choices", [{}])[0].get("text", "")
                else:
                    error_text = await response.text()
                    raise Exception(f"Copilot completion error: {response.status} - {error_text}")