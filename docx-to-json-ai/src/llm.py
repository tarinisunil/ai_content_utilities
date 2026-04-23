import logging
import os
from dotenv import load_dotenv
from openai import OpenAI

logger = logging.getLogger(__name__)
load_dotenv()

MODEL_ID = "openai/gpt-oss-20b:free"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set")

logger.info("Loading OpenRouter client: model=%s", MODEL_ID)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


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
        max_tokens=256,
    )

    logger.info("generate_json: router selected model=%s", getattr(response, "model", MODEL_ID))

    generated = response.choices[0].message.content or ""

    logger.info(
        "generate_json: inference complete, generated_text length=%d",
        len(generated),
    )
    logger.info("generate_json: full output:\n%s", generated)
    return generated