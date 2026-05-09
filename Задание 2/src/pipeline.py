from __future__ import annotations

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv() -> None:
        return None


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model: str


def load_config() -> LLMConfig:
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()

    if provider == "ollama":
        return LLMConfig(
            provider=provider,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/"),
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
        )

    return LLMConfig(
        provider="openrouter",
        base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/"),
        api_key=os.getenv("OPENROUTER_API_KEY", ""),
        model=os.getenv("OPENROUTER_MODEL", "qwen/qwen3.6-plus"),
    )


def read_reviews(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def build_messages(batch: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You classify product reviews for a data analytics assignment. "
                "Return only valid JSON. Do not include Markdown. "
                "Use this schema: {\"items\":[{\"id\":\"string\",\"sentiment\":\"positive|negative|neutral\","
                "\"topic\":\"short topic in Russian\",\"confidence\":0.0,\"reason\":\"one short Russian sentence\"}]}."
            ),
        },
        {
            "role": "user",
            "content": "Classify these Russian reviews:\n" + json.dumps(batch, ensure_ascii=False),
        },
    ]


def call_llm(config: LLMConfig, messages: list[dict[str, str]]) -> dict:
    if not config.api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Copy .env.example to .env and add the key.")

    body = {
        "model": config.model,
        "messages": messages,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        f"{config.base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/eazyan/data-analyst-llm",
            "X-Title": "Data Analyst LLM Assignment",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API error {error.code}: {details}") from error

    content = payload["choices"][0]["message"]["content"]
    return json.loads(content)


def validate_result(result: dict, expected_ids: set[str]) -> dict:
    if not isinstance(result, dict) or not isinstance(result.get("items"), list):
        raise ValueError("LLM result must contain an 'items' array.")

    allowed_sentiments = {"positive", "negative", "neutral"}
    seen_ids: set[str] = set()
    for item in result["items"]:
        if item.get("id") not in expected_ids:
            raise ValueError(f"Unexpected id in LLM result: {item.get('id')}")
        if item.get("sentiment") not in allowed_sentiments:
            raise ValueError(f"Invalid sentiment for id {item.get('id')}: {item.get('sentiment')}")
        if not isinstance(item.get("topic"), str) or not item["topic"].strip():
            raise ValueError(f"Missing topic for id {item.get('id')}")
        confidence = item.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError(f"Invalid confidence for id {item.get('id')}: {confidence}")
        seen_ids.add(item["id"])

    missing = expected_ids - seen_ids
    if missing:
        raise ValueError(f"Missing ids in LLM result: {sorted(missing)}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify Russian reviews with an LLM API.")
    parser.add_argument("--input", type=Path, default=ROOT / "input" / "reviews.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "output" / "reviews_classified.json")
    args = parser.parse_args()

    reviews = read_reviews(args.input)
    expected_ids = {row["id"] for row in reviews}
    config = load_config()

    started_at = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    result = call_llm(config, build_messages(reviews))
    validated = validate_result(result, expected_ids)

    output = {
        "metadata": {
            "task": "review_sentiment_and_topic_classification",
            "provider": config.provider,
            "model": config.model,
            "input_file": str(args.input),
            "created_at": started_at,
        },
        "result": validated,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(validated['items'])} classified reviews to {args.output}")


if __name__ == "__main__":
    main()
