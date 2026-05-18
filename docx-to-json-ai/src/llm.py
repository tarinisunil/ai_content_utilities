from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)
load_dotenv()

# Defaults can be overridden via environment variables.
# Suggested local Ollama model for this project:
#   llama3.2:3b
# Suggested OpenRouter model for this project:
#   openai/gpt-oss-20b:free
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip()
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OLLAMA_THINK = os.getenv("OLLAMA_THINK", "false").strip().lower() in {"1", "true", "yes", "on"}

CURRENT_PROVIDER = DEFAULT_PROVIDER
CURRENT_MODEL = OPENROUTER_MODEL
client: Optional[OpenAI] = None


def _make_client(provider: str) -> OpenAI:
    provider = provider.strip().lower()

    if provider == "ollama":
        return OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",
        )

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not set")

    return OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
    )


def configure_provider(provider: str, model: Optional[str] = None) -> None:
    """
    Configure the active provider and model.

    provider:
        "openrouter" or "ollama"
    model:
        Optional override for the provider's default model.
    """
    global client, CURRENT_PROVIDER, CURRENT_MODEL

    provider = (provider or "").strip().lower()
    if provider not in {"openrouter", "ollama"}:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    CURRENT_PROVIDER = provider

    if provider == "ollama":
        CURRENT_MODEL = (model or OLLAMA_MODEL).strip()
    else:
        CURRENT_MODEL = (model or OPENROUTER_MODEL).strip()

    client = _make_client(provider)

    logger.info(
        "Configured LLM provider=%s model=%s base_url=%s",
        CURRENT_PROVIDER,
        CURRENT_MODEL,
        OLLAMA_BASE_URL if provider == "ollama" else OPENROUTER_BASE_URL,
    )


def get_provider() -> str:
    return CURRENT_PROVIDER


def get_model_name() -> str:
    return CURRENT_MODEL


def _message_content(message: Any) -> str:
    """
    Extract generated text from a chat completion message.
    Tries common fields used by OpenAI-compatible backends.
    """
    if message is None:
        return ""

    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()

    reasoning = getattr(message, "reasoning_content", None)
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
            elif isinstance(item, str) and item.strip():
                parts.append(item.strip())
        if parts:
            return "\n".join(parts).strip()

    return ""


def _call_chat_completion(prompt: str, *, provider: Optional[str] = None, model: Optional[str] = None) -> str:
    active_provider = (provider or CURRENT_PROVIDER).strip().lower()
    active_model = (model or CURRENT_MODEL).strip()

    if active_provider not in {"openrouter", "ollama"}:
        raise ValueError(f"Unsupported LLM provider: {active_provider}")

    if client is None or active_provider != CURRENT_PROVIDER or (model and active_model != CURRENT_MODEL):
        configure_provider(active_provider, active_model)

    assert client is not None

    extra_body: Dict[str, Any] | None = None
    if active_provider == "ollama" and OLLAMA_THINK is False:
        # For some local models, disabling "thinking" avoids empty final content.
        extra_body = {"think": False}

    logger.info(
        "generate_json: provider=%s model=%s prompt_chars=%d",
        active_provider,
        active_model,
        len(prompt),
    )

    kwargs: Dict[str, Any] = {
        "model": active_model,
        "messages": [
            {
                "role": "system",
                "content": "You are an information extraction system. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0,
        "top_p": 1,
        "max_tokens": 1024,
    }

    if extra_body:
        kwargs["extra_body"] = extra_body

    response = client.chat.completions.create(**kwargs)

    logger.info("generate_json: model=%s", getattr(response, "model", active_model))

    if hasattr(response, "model_dump"):
        try:
            logger.debug("generate_json: full response=%s", response.model_dump())
        except Exception:
            pass

    message = response.choices[0].message
    generated = _message_content(message)

    if not generated:
        response_dump = None
        if hasattr(response, "model_dump"):
            try:
                response_dump = response.model_dump()
            except Exception:
                response_dump = None

        logger.error("generate_json: empty output from provider=%s model=%s", active_provider, active_model)
        if response_dump is not None:
            logger.error("generate_json: full response dump=%s", response_dump)
        raise RuntimeError(f"Model returned empty output: provider={active_provider}, model={active_model}")

    logger.info("generate_json: inference complete, generated_text length=%d", len(generated))
    logger.debug("generate_json: full output:\n%s", generated)
    return generated


def generate_json(prompt: str, provider: Optional[str] = None, model: Optional[str] = None) -> str:
    """
    Generate raw text from the configured LLM provider.
    The caller is expected to parse JSON from the returned text.
    """
    return _call_chat_completion(prompt, provider=provider, model=model)


# Initialize on import.
configure_provider(DEFAULT_PROVIDER)
