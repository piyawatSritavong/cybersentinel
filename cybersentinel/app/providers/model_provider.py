import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """Abstract base class for all AI model providers."""

    name: str = "base"
    display_name: str = "Base Provider"

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "configured": self.is_configured(),
            "models": self.get_models(),
        }


class GroqProvider(BaseModelProvider):
    """Groq AI provider using existing Groq logic."""

    name = "groq"
    display_name = "Groq"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        if not self._api_key:
            try:
                from app.core.config import settings
                self._api_key = settings.groq_api_key
            except Exception:
                self._api_key = ""

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        if not self.is_configured():
            return "Groq provider not configured - missing API key"

        try:
            from langchain_groq import ChatGroq

            target_model = model or "llama-3.3-70b-versatile"
            llm = ChatGroq(
                api_key=self._api_key,
                model_name=target_model,
                temperature=0.1,
            )

            prompt = "\n".join(
                f"{m.get('role', 'user')}: {m.get('content', '')}"
                for m in messages
            )
            response = llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"[GROQ] Chat error: {e}")
            return f"Groq chat failed: {str(e)}"

    def get_models(self) -> List[str]:
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key != "mock" and len(self._api_key) > 5)


class OpenAIProvider(BaseModelProvider):
    """OpenAI provider stub."""

    name = "openai"
    display_name = "OpenAI"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        if not self.is_configured():
            return "OpenAI provider not configured"
        return "OpenAI provider not yet implemented"

    def get_models(self) -> List[str]:
        return ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 5)


class AnthropicProvider(BaseModelProvider):
    """Anthropic provider stub."""

    name = "anthropic"
    display_name = "Anthropic"

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        if not self.is_configured():
            return "Anthropic provider not configured"
        return "Anthropic provider not yet implemented"

    def get_models(self) -> List[str]:
        return ["claude-3.5-sonnet", "claude-3-haiku", "claude-3-opus"]

    def is_configured(self) -> bool:
        return bool(self._api_key and len(self._api_key) > 5)


class OllamaProvider(BaseModelProvider):
    """Ollama local model provider stub."""

    name = "ollama"
    display_name = "Ollama (Local)"

    def __init__(self, base_url: str = ""):
        self._base_url = base_url
        if not self._base_url:
            try:
                from app.core.config import settings
                self._base_url = settings.ollama_base_url
            except Exception:
                self._base_url = "http://localhost:11434"

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        if not self.is_configured():
            return "Ollama provider not configured - cannot reach server"
        return "Ollama provider not yet implemented"

    def get_models(self) -> List[str]:
        return ["llama3", "mistral", "codellama", "phi3"]

    def is_configured(self) -> bool:
        if not self._base_url:
            return False
        try:
            import urllib.request
            req = urllib.request.Request(f"{self._base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3):
                return True
        except Exception:
            return False


_PROVIDERS = {
    "groq": GroqProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def get_model_provider(name: str, **kwargs) -> BaseModelProvider:
    """Factory function to get a model provider by name."""
    provider_cls = _PROVIDERS.get(name.lower())
    if not provider_cls:
        raise ValueError(f"Unknown model provider: {name}. Available: {list(_PROVIDERS.keys())}")
    return provider_cls(**kwargs)


def list_providers() -> List[Dict[str, Any]]:
    """Returns all providers with their current status."""
    results = []
    for name, cls in _PROVIDERS.items():
        try:
            provider = cls()
            status = provider.get_status()
            results.append(status)
        except Exception as e:
            results.append({
                "name": name,
                "display_name": name.title(),
                "configured": False,
                "models": [],
                "error": str(e),
            })
    return results
