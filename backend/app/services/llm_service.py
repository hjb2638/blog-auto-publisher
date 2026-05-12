import json
import re
import time

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.prompts.system import SYSTEM_PROMPT
from app.utils.logger import logger


def _is_retryable(e: BaseException) -> bool:
    if isinstance(e, httpx.HTTPStatusError):
        return e.response.status_code in {429, 500, 502, 503, 504}
    return isinstance(e, (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError))


class LLMService:
    def __init__(self):
        self.base_url = settings.llm_base_url.rstrip("/")
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature
        self.timeout = settings.llm_timeout

    def _build_messages(self, user_prompt: str) -> list[dict]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

    @retry(
        retry=retry_if_exception(_is_retryable),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _call(self, messages: list[dict]) -> dict:
        start = time.monotonic()
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            )
            resp.raise_for_status()
        elapsed_ms = int((time.monotonic() - start) * 1000)
        data = resp.json()
        choice = data["choices"][0]
        return {
            "content": choice["message"]["content"],
            "tokens_input": data.get("usage", {}).get("prompt_tokens", 0),
            "tokens_output": data.get("usage", {}).get("completion_tokens", 0),
            "latency_ms": elapsed_ms,
            "finish_reason": choice.get("finish_reason", "unknown"),
        }

    async def generate_response(self, user_prompt: str) -> dict:
        messages = self._build_messages(user_prompt)
        logger.info("LLM call: model=%s prompt_len=%d", self.model, len(user_prompt))
        return await self._call(messages)

    async def generate_json(self, user_prompt: str) -> dict:
        result = await self.generate_response(user_prompt)
        content = result["content"]
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            data = self._lenient_json_parse(content)
        result["parsed"] = data
        return result

    def _lenient_json_parse(self, text: str) -> dict:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if not match:
            match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse LLM JSON response: {text[:500]}")


llm_service = LLMService()
