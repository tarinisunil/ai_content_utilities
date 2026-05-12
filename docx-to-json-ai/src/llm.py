import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)
load_dotenv()

# Provider defaults — can be overridden via .env or configure_provider()
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Module-level state updated by configure_provider()
MODEL_ID: str = OPENROUTER_MODEL
client: OpenAI = None  # type: ignore[assignment]


def configure_provider(provider: str, model: str | None = None) -> None:
    global client, MODEL_ID

    if provider == "ollama":
        MODEL_ID = model or OLLAMA_MODEL
        client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")
        logger.info("Configured Ollama client: base_url=%s model=%s", OLLAMA_BASE_URL, MODEL_ID)
    else:
        MODEL_ID = model or OPENROUTER_MODEL
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not set")
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
        logger.info("Configured OpenRouter client: model=%s", MODEL_ID)


# Initialize from env on import
configure_provider(LLM_PROVIDER)


def generate_json(prompt: str) -> str:
    logger.info("generate_json: running inference, prompt_chars=%d", len(prompt))

    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {
                "role": "system",
                "content": "You are an information extraction system. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        top_p=1,
        max_tokens=1024,
    )

    logger.info("generate_json: model=%s", getattr(response, "model", MODEL_ID))

    generated = response.choices[0].message.content or ""

    logger.info(
        "generate_json: inference complete, generated_text length=%d",
        len(generated),
    )
    logger.info("generate_json: full output:\n%s", generated)
    return generated
