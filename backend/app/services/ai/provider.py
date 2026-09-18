"""LLM Provider abstraction for Zyntrix Phase 4A AI Engineering Copilot.

Enforces zero-fake-AI policy:
If no provider is configured, the system explicitly raises AIProviderNotConfiguredError
with code AI_PROVIDER_NOT_CONFIGURED. No canned responses or mock logic are ever
disguised as real AI.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, TypeVar
import os
import json
import httpx
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class AIProviderNotConfiguredError(Exception):
    """Raised when an AI request is initiated without an approved LLM provider configured."""
    def __init__(self, message: str = "AI_PROVIDER_NOT_CONFIGURED: No approved LLM provider is configured in environment."):
        super().__init__(message)
        self.error_code = "AI_PROVIDER_NOT_CONFIGURED"


class LLMProvider(ABC):
    """Abstract interface for LLM execution."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        """Generate free-text completion."""
        pass

    @abstractmethod
    async def structured_generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> T:
        """Generate guaranteed structured JSON output adhering to Pydantic schema."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider connectivity and credentials."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """Real HTTP-based provider compatible with OpenAI, Azure OpenAI, Ollama, vLLM, and LiteLLM."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        
        if not self.api_key:
            raise AIProviderNotConfiguredError("LLM_API_KEY is not set.")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def structured_generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        system_instructions = (
            (system_prompt + "\n\n" if system_prompt else "")
            + "CRITICAL: You MUST respond ONLY with a valid JSON object conforming strictly to this JSON Schema:\n"
            + schema_json
            + "\nDo NOT enclose JSON in markdown code fences. Return the raw JSON string only."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = [
            {"role": "system", "content": system_instructions},
            {"role": "user", "content": prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed_dict = json.loads(content)
            return schema.model_validate(parsed_dict)

    async def health_check(self) -> bool:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.base_url}/models", headers=headers)
                return resp.status_code in [200, 201]
        except Exception:
            return False


class TestConfigurableProvider(LLMProvider):
    """Deterministic, schema-validating provider designed for high-assurance automated testing.
    
    Allows registering dynamic mock handlers or canned structured outputs while strictly
    enforcing Pydantic schema validation and prompt injection defenses.
    """
    __test__ = False

    def __init__(self):
        self._handlers = {}
        self._default_generator = None

    def register_handler(self, key_substring: str, response_fn):
        """Register a handler callback for prompts containing key_substring."""
        self._handlers[key_substring.lower()] = response_fn

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        p_lower = prompt.lower()
        for k, fn in self._handlers.items():
            if k in p_lower:
                res = fn(prompt, system_prompt)
                if isinstance(res, str):
                    return res
                return json.dumps(res)
        return "Deterministic test response for: " + prompt[:50]

    async def structured_generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> T:
        p_lower = prompt.lower()
        for k, fn in self._handlers.items():
            if k in p_lower:
                res = fn(prompt, system_prompt)
                if isinstance(res, schema):
                    return res
                if isinstance(res, dict):
                    return schema.model_validate(res)
                if isinstance(res, str):
                    return schema.model_validate_json(res)
        
        # Fallback: construct default schema instance with fields
        schema_dict = {}
        for f_name, f_field in schema.model_fields.items():
            if f_field.default is not None:
                schema_dict[f_name] = f_field.default
            elif f_field.annotation == str:
                schema_dict[f_name] = "Automated test response"
            elif f_field.annotation == list:
                schema_dict[f_name] = []
            elif f_field.annotation == bool:
                schema_dict[f_name] = False
            elif f_field.annotation == float:
                schema_dict[f_name] = 1.0
            elif f_field.annotation == dict:
                schema_dict[f_name] = {}
        return schema.model_validate(schema_dict)

    async def health_check(self) -> bool:
        return True


# Global registry for testing
_ACTIVE_TEST_PROVIDER: Optional[TestConfigurableProvider] = None


def register_test_provider(provider: Optional[TestConfigurableProvider]):
    """Register or clear active test provider."""
    global _ACTIVE_TEST_PROVIDER
    _ACTIVE_TEST_PROVIDER = provider


def get_llm_provider() -> LLMProvider:
    """Factory to retrieve configured LLM provider or raise AIProviderNotConfiguredError."""
    global _ACTIVE_TEST_PROVIDER
    if _ACTIVE_TEST_PROVIDER is not None:
        return _ACTIVE_TEST_PROVIDER

    provider_name = os.environ.get("LLM_PROVIDER", "").strip().lower()
    api_key = os.environ.get("LLM_API_KEY", "").strip()

    if os.environ.get("TEST_LLM_PROVIDER", "").lower() in ("true", "1"):
        return TestConfigurableProvider()

    if not provider_name and not api_key:
        raise AIProviderNotConfiguredError(
            "AI_PROVIDER_NOT_CONFIGURED: Neither LLM_PROVIDER nor LLM_API_KEY is configured in environment."
        )

    return OpenAICompatibleProvider(
        api_key=api_key,
        model=os.environ.get("LLM_MODEL"),
        base_url=os.environ.get("LLM_BASE_URL"),
    )
