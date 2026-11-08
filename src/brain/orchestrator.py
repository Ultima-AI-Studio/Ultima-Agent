"""Fail-closed DeepSeek stage runner for G-ORCH stages 2, 3, and 4."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential
from tenacity.nap import sleep


DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
STAGE_SYSTEM_PROMPTS = {
    "decompose": (
        "You are the independent G-ORCH stage 2 agent. Decompose the approved plan, "
        "verify dependencies and non-overlapping write domains, and return a verdict."
    ),
    "work_order": (
        "You are the independent G-ORCH stage 3 agent. Produce and self-check a work "
        "order whose six definition-of-ready gates are objectively decidable."
    ),
    "schedule": (
        "You are the independent G-ORCH stage 4 agent. Schedule ready work orders while "
        "respecting dependencies, WIP limits, and available execution capacity."
    ),
}


class OrchestratorError(RuntimeError):
    """Raised when an orchestration stage cannot produce valid durable output."""


class _RetryableDeepSeekError(RuntimeError):
    """Internal marker for the only failures eligible for retry."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _request_once(
    system_prompt: str,
    prompt: str,
    *,
    api_key: str,
    model: str,
    max_tokens: int,
    timeout: float,
) -> dict[str, Any]:
    try:
        response = requests.post(
            DEEPSEEK_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise _RetryableDeepSeekError("DeepSeek request timed out") from exc
    except requests.RequestException as exc:
        raise OrchestratorError(f"DeepSeek request failed: {type(exc).__name__}") from exc

    if response.status_code == 429 or response.status_code >= 500:
        raise _RetryableDeepSeekError(f"DeepSeek HTTP {response.status_code}")
    if response.status_code != 200:
        raise OrchestratorError(f"DeepSeek HTTP {response.status_code}")

    try:
        payload = response.json()
    except (TypeError, ValueError) as exc:
        raise OrchestratorError("DeepSeek returned invalid JSON") from exc

    try:
        content = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        raise OrchestratorError("DeepSeek returned an invalid response schema") from exc

    if not isinstance(content, str) or not content.strip():
        raise OrchestratorError("DeepSeek returned empty content")

    return {
        "model": model,
        "response": content,
        "tokens": {"in": input_tokens, "out": output_tokens},
    }


def call_deepseek(
    system_prompt: str,
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Call one isolated DeepSeek conversation and return normalized output."""

    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise OrchestratorError("DEEPSEEK_API_KEY is required")

    retrying = Retrying(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type(_RetryableDeepSeekError),
        sleep=sleep,
        reraise=True,
    )
    try:
        for attempt in retrying:
            with attempt:
                return _request_once(
                    system_prompt,
                    prompt,
                    api_key=api_key,
                    model=model,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
    except _RetryableDeepSeekError as exc:
        raise OrchestratorError(f"DeepSeek request failed after 3 attempts: {exc}") from exc

    raise OrchestratorError("DeepSeek retry loop ended without a result")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_stage(
    stage: str,
    prompt: str,
    run_dir: str | Path,
    *,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 4096,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Run one stage with fresh system context and persist its durable receipt."""

    stages_dir = Path(run_dir) / "stages"
    failed_path = stages_dir / f"{stage}-failed.json"
    started = time.monotonic()

    try:
        system_prompt = STAGE_SYSTEM_PROMPTS[stage]
        result = call_deepseek(
            system_prompt,
            prompt,
            model=model,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        artifact = {
            "stage": stage,
            "model": result["model"],
            "system_digest": hashlib.sha256(system_prompt.encode("utf-8")).hexdigest(),
            "prompt": prompt,
            "response": result["response"],
            "tokens": result["tokens"],
            "elapsed_s": round(time.monotonic() - started, 6),
            "verdict": "completed",
            "created_at": _utc_now(),
        }
        _write_json(stages_dir / f"{stage}.json", artifact)
        return artifact
    except Exception as exc:
        error = exc if isinstance(exc, OrchestratorError) else OrchestratorError(str(exc))
        _write_json(
            failed_path,
            {
                "stage": stage,
                "model": model,
                "error": str(error),
                "created_at": _utc_now(),
            },
        )
        raise error from exc


__all__ = [
    "DEFAULT_MODEL",
    "DEEPSEEK_URL",
    "OrchestratorError",
    "STAGE_SYSTEM_PROMPTS",
    "call_deepseek",
    "run_stage",
]
