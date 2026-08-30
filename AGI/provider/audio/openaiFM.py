# AGI Provider - OpenAI FM (Fine-tuned Models)
# OpenAI-এর Fine-tuned মডেলগুলোর জন্য প্রোভাইডার

from __future__ import annotations

import json
import aiohttp
from typing import AsyncGenerator, Optional, Dict, Any

from ...typing import AsyncResult, Messages
from ..base_provider import AsyncGeneratorProvider, ProviderModelMixin
from ..helper import get_last_message


class OpenAI_FM(AsyncGeneratorProvider, ProviderModelMixin):
    """
    OpenAI Fine-tuned Models প্রোভাইডার
    কাস্টম ফাইন-টিউন করা GPT মডেলগুলো চালানোর জন্য
    """
    
    label = "OpenAI FM (Fine-tuned)"
    working = True
    url = "https://api.openai.com/v1"
    
    # ডিফল্ট মডেল
    model_id = "gpt-3.5-turbo"
    default_model = "gpt-3.5-turbo"
    
    @classmethod
    def get_models(cls) -> list[str]:
        """উপলব্ধ ফাইন-টিউন মডেলের লিস্ট"""
        return [
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo-preview",
            "gpt-4o",
            "gpt-4o-mini"
        ]
    
    @classmethod
    async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        prompt: str = None,
        api_key: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stream: bool = True,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        OpenAI API ব্যবহার করে রেসপন্স জেনারেট করে
        """
        if not api_key:
            raise ValueError("OpenAI API key is required. Please provide api_key parameter.")
        
        prompt = get_last_message(messages, prompt)
        if not prompt:
            raise ValueError("Prompt is empty.")
        
        # API এন্ডপয়েন্ট
        endpoint = f"{cls.url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model if model else cls.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "stream": stream
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"OpenAI API error: {response.status} - {error_text}")
                
                if stream:
                    # স্ট্রিমিং রেসপন্স
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
                    # নন-স্ট্রিমিং রেসপন্স
                    json_data = await response.json()
                    content = json_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    yield content
    
    @classmethod
    async def list_fine_tuned_models(cls, api_key: str) -> list:
        """ফাইন-টিউন করা মডেলের লিস্ট দেখায়"""
        endpoint = f"{cls.url}/fine_tuning/jobs"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(endpoint, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", [])
                else:
                    error_text = await response.text()
                    raise Exception(f"Error fetching fine-tuned models: {response.status} - {error_text}")