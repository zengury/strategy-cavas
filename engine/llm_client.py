"""
LLM 客户端 — AsyncOpenAI 封装，负责 API 调用和重试逻辑。

从 conversation.py 提取，v2 重构。
"""

import logging
from openai import AsyncOpenAI

log = logging.getLogger("llm_client")


class LLMClient:
    """DeepSeek API 的轻量封装，支持重试和超时。"""

    MAX_RETRIES = 2

    def __init__(self, api_key: str, api_base: str = "https://api.deepseek.com"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=api_base)

    async def chat(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        *,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """发送聊天请求，带重试。"""
        last_error = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    log.warning(f"LLM call attempt {attempt + 1} failed, retrying: {e}")
                    import asyncio
                    await asyncio.sleep(1.0 * (attempt + 1))
        raise last_error

    async def route(
        self,
        model: str,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> str:
        """发送路由请求（零温度、少 token）。"""
        response = await self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
