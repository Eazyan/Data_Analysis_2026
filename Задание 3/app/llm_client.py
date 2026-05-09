from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from config import LLMConfig


PYTHON_TOOL = {
    "type": "function",
    "function": {
        "name": "run_python_code",
        "description": (
            "Run Python code to analyze the uploaded dataset. Use pandas and matplotlib. "
            "The variable DATASET_PATH contains the uploaded file path and OUTPUT_DIR contains "
            "a directory where charts can be saved."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code that prints concise findings and saves charts into OUTPUT_DIR.",
                }
            },
            "required": ["code"],
        },
    },
}


def chat_completion(
    config: LLMConfig,
    messages: list[dict[str, Any]],
    *,
    tools: bool,
    require_tool: bool = False,
) -> dict[str, Any]:
    if not config.api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to .env or environment variables.")

    body: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": 0.2,
    }
    if tools:
        body["tools"] = [PYTHON_TOOL]
        body["tool_choice"] = (
            {"type": "function", "function": {"name": "run_python_code"}}
            if require_tool
            else "auto"
        )

    request = urllib.request.Request(
        f"{config.base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/eazyan/data-analyst-llm",
            "X-Title": "LLM Data Analyst Agent",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API error {error.code}: {details}") from error


def extract_message(payload: dict[str, Any]) -> dict[str, Any]:
    return payload["choices"][0]["message"]
