"""Unified LLM client supporting multiple providers"""

import asyncio
from typing import AsyncIterator, Optional, Dict, Any, List, Union
from abc import ABC, abstractmethod
from openai import AsyncOpenAI, AsyncStream
from anthropic import AsyncAnthropic
from src.config import settings
import structlog

logger = structlog.get_logger(__name__)


class BaseLLMClient(ABC):
    """Base class for LLM clients"""

    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Get streaming chat completion"""
        pass

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> str:
        """Get non-streaming chat completion"""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI client"""

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Get streaming chat completion from OpenAI"""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **kwargs
        )

        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> str:
        """Get non-streaming chat completion from OpenAI"""
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            **kwargs
        )
        return response.choices[0].message.content


class AnthropicClient(BaseLLMClient):
    """Anthropic client"""

    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> AsyncIterator[str]:
        """Get streaming chat completion from Anthropic"""
        # Convert messages to Anthropic format
        system_message = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        response = await self.client.messages.create(
            model=model,
            system=system_message,
            messages=user_messages,
            stream=True,
            max_tokens=4096,
            **kwargs
        )

        async for chunk in response:
            if chunk.type == "content_block_delta":
                yield chunk.delta.text

    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        **kwargs
    ) -> str:
        """Get non-streaming chat completion from Anthropic"""
        # Convert messages to Anthropic format
        system_message = ""
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        response = await self.client.messages.create(
            model=model,
            system=system_message,
            messages=user_messages,
            stream=False,
            max_tokens=4096,
            **kwargs
        )
        return response.content[0].text


class LLMClientFactory:
    """Factory for creating LLM clients"""

    _clients: Dict[str, BaseLLMClient] = {}

    @classmethod
    def get_client(cls, provider: str = None) -> BaseLLMClient:
        """Get LLM client for provider"""
        provider = provider or settings.default_llm_provider

        if provider in cls._clients:
            return cls._clients[provider]

        if provider == "openai":
            client = OpenAIClient(api_key=settings.openai_api_key)
        elif provider == "anthropic":
            client = AnthropicClient(api_key=settings.anthropic_api_key)
        elif provider == "qwen":
            client = OpenAIClient(api_key=settings.api_key, base_url=settings.base_url)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        cls._clients[provider] = client
        logger.info("LLM client initialized", provider=provider)
        return client


async def get_llm_response(
    messages: List[Dict[str, Any]],
    model: str = None,
    provider: str = None,
) -> str:
    """Get non-streaming LLM response"""
    model = model or settings.default_model
    client = LLMClientFactory.get_client(provider)

    logger.info("LLM request", model=model, provider=provider, stream=False)

    return await client.chat_completion(messages, model)


async def get_llm_response_stream(
    messages: List[Dict[str, Any]],
    model: str = None,
    provider: str = None,
) -> AsyncIterator[str]:
    """Get streaming LLM response"""
    model = model or settings.default_model
    client = LLMClientFactory.get_client(provider)

    logger.info("LLM request", model=model, provider=provider, stream=True)

    async for chunk in client.chat_completion_stream(messages, model):
        yield chunk
