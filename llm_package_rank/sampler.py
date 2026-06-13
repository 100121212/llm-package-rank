from __future__ import annotations

import json
from pathlib import Path
from urllib import error, request


DEVELOPER_INSTRUCTIONS = (
    "You are helping benchmark package recommendations. "
    "Answer with concise package recommendations and short reasons. "
    "Prefer open-source packages when possible."
)


def build_prompt(task: dict) -> str:
    return (
        f"{DEVELOPER_INSTRUCTIONS}\n\n"
        f"Task id: {task['id']}\n"
        f"Developer task: {task['prompt']}\n\n"
        "Recommend packages a developer should evaluate."
    )


def estimate_tokens(text: str) -> int:
    # Simple offline estimate: roughly four characters per token.
    return max(1, (len(text) + 3) // 4)


def estimate_run(tasks: list[dict], model: str, max_output_tokens: int) -> dict:
    prompts = [build_prompt(task) for task in tasks]
    input_tokens = sum(estimate_tokens(prompt) for prompt in prompts)
    output_tokens = len(tasks) * max_output_tokens
    return {
        "model": model,
        "task_count": len(tasks),
        "estimated_input_tokens": input_tokens,
        "max_output_tokens": output_tokens,
        "estimated_total_tokens": input_tokens + output_tokens,
    }


def collect_responses(tasks: list[dict], model: str, max_output_tokens: int, client) -> list[dict]:
    responses = []
    for task in tasks:
        answer = client.create_response(
            model=model,
            prompt=build_prompt(task),
            max_output_tokens=max_output_tokens,
        )
        responses.append(
            {
                "task_id": task["id"],
                "model": model,
                "answer": answer,
            }
        )
    return responses


def extract_output_text(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    chunks: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    if chunks:
        return "\n".join(chunks).strip()
    raise ValueError("response did not contain output text")


class OpenAIResponsesClient:
    def __init__(self, api_key: str, endpoint: str = "https://api.openai.com/v1/responses", timeout: int = 60):
        self.api_key = api_key
        self.endpoint = endpoint
        self.timeout = timeout

    def create_response(self, model: str, prompt: str, max_output_tokens: int) -> str:
        payload = {
            "model": model,
            "input": prompt,
            "max_output_tokens": max_output_tokens,
        }
        req = request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenAI API request failed with HTTP {exc.code}: {message}") from exc
        return extract_output_text(json.loads(body))


def read_tasks(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        tasks = json.load(handle)
    if not isinstance(tasks, list):
        raise ValueError("tasks JSON must be a list")
    return tasks
