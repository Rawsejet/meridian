"""Client for the local llama.cpp server (OpenAI-compatible API)."""
import httpx
import logging
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for the local llama.cpp server (OpenAI-compatible API)."""

    def __init__(
        self,
        base_url: str,
        max_tokens: int = 2048,
        temperature: float = 0.1,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout
        self.http = httpx.AsyncClient(
            base_url=self.base_url, timeout=timeout, headers={"Content-Type": "application/json"}
        )

    async def complete(
        self,
        messages: list[dict],
        *,
        max_tokens: int | None = None,
        temperature: float | None = None,
        json_mode: bool = False,
    ) -> str:
        """
        Send a chat completion request. Returns the assistant's text.

        messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
        json_mode: if True, requests JSON output format
        """
        payload = {
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = await self.http.post("/v1/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()

        content = data["choices"][0]["message"]["content"]

        usage = data.get("usage", {})
        logger.info(
            "LLM call: tokens_in=%d tokens_out=%d",
            usage.get("prompt_tokens", 0),
            usage.get("completion_tokens", 0),
        )

        return content

    async def complete_json(self, messages: list[dict], **kwargs) -> dict:
        """Complete and parse as JSON. Raises ValueError if parse fails."""
        text = await self.complete(messages, json_mode=True, **kwargs)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(text)

    async def health_check(self) -> bool:
        """Check if llama.cpp is responding."""
        try:
            resp = await self.http.get("/health")
            return resp.status_code == 200
        except httpx.HTTPError:
            return False

    async def close(self):
        await self.http.aclose()


# --- Singleton ---

_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    global _client
    if _client is None:
        from app.core.config import get_settings

        s = get_settings()
        _client = LLMClient(
            base_url=s.llm_base_url,
            max_tokens=s.llm_max_tokens,
            temperature=s.llm_temperature,
            timeout=s.llm_timeout_seconds,
        )
    return _client


async def reset_llm_client():
    """Reset the singleton client (useful for testing)."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None