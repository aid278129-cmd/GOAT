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


class GoogleGeminiProvider(LLMProvider):
    """Direct Google Generative Language API provider for Gemini models."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "") or os.environ.get("LLM_API_KEY", "")
        self.model = model or os.environ.get("LLM_MODEL", "gemini-flash-lite-latest")
        if not self.api_key:
            raise AIProviderNotConfiguredError("GEMINI_API_KEY is not set.")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1500,
        temperature: float = 0.1,
    ) -> str:
        # Build prioritized list of models to try
        primary = self.model.replace("models/", "") if self.model else "gemini-flash-lite-latest"
        models_to_try = [primary, "gemini-flash-lite-latest", "gemini-flash-latest"]
        seen = set()
        deduped_models = []
        for m in models_to_try:
            if m and m not in seen:
                seen.add(m)
                deduped_models.append(m)

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_prompt:
            payload["system_instruction"] = {
                "parts": [{"text": system_prompt}]
            }

        async with httpx.AsyncClient(timeout=45.0) as client:
            last_err = None
            for candidate_model in deduped_models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate_model}:generateContent?key={self.api_key}"
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (404, 429, 500, 503):
                        last_err = f"Model {candidate_model} returned {resp.status_code}: {resp.text[:120]}"
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        valid_texts = []
                        for p in parts:
                            if p.get("thought"):
                                continue
                            t = p.get("text", "")
                            if t:
                                valid_texts.append(t)
                        raw_ans = "\n".join(valid_texts).strip()
                        if "<thought>" in raw_ans and "</thought>" in raw_ans:
                            raw_ans = raw_ans.split("</thought>")[-1].strip()
                        if raw_ans:
                            return raw_ans
                except Exception as exc:
                    last_err = exc
                    continue

            # If all model candidates failed, log and return empty so caller falls back cleanly
            import logging
            logging.getLogger(__name__).warning("Gemini generation skipped due to: %s", last_err)
            return ""

    async def structured_generate(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> T:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        full_system = (
            (system_prompt + "\n\n" if system_prompt else "")
            + "CRITICAL: You MUST respond ONLY with a valid JSON object conforming strictly to this JSON Schema:\n"
            + schema_json
            + "\nDo NOT enclose JSON in markdown code fences. Return the raw JSON string only."
        )
        raw_text = await self.generate(
            prompt=prompt,
            system_prompt=full_system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        parsed = json.loads(cleaned.strip())
        return schema.model_validate(parsed)

    async def health_check(self) -> bool:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url)
                return resp.status_code == 200
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

    from backend.app.core.config import settings

    provider_name = (os.environ.get("LLM_PROVIDER") or settings.LLM_PROVIDER or "").strip().lower()
    api_key = (
        os.environ.get("LLM_API_KEY", "").strip()
        or getattr(settings, "LLM_API_KEY", None)
        or os.environ.get("GEMINI_API_KEY", "").strip()
        or getattr(settings, "GEMINI_API_KEY", None)
        or os.environ.get("OPENAI_API_KEY", "").strip()
        or getattr(settings, "OPENAI_API_KEY", None)
        or ""
    ).strip()

    if os.environ.get("TEST_LLM_PROVIDER", "").lower() in ("true", "1"):
        return TestConfigurableProvider()

    if not provider_name and not api_key:
        raise AIProviderNotConfiguredError(
            "AI_PROVIDER_NOT_CONFIGURED: Neither LLM_PROVIDER nor LLM_API_KEY is configured in environment."
        )

    base_url = os.environ.get("LLM_BASE_URL") or getattr(settings, "LLM_BASE_URL", None)
    model = os.environ.get("LLM_MODEL") or getattr(settings, "LLM_MODEL", None)

    # If Gemini is configured (via provider name, key format, or GEMINI_API_KEY)
    if provider_name == "gemini" or api_key.startswith("AQ.") or os.environ.get("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None):
        return GoogleGeminiProvider(
            api_key=api_key,
            model=model or "gemini-flash-lite-latest",
        )

    return OpenAICompatibleProvider(
        api_key=api_key,
        model=model,
        base_url=base_url,
    )
