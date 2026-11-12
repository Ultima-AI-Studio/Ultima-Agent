"""Bounded connectivity checks for effective S-MAIN settings."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen

from ..slot_adapter import main_chat_url
from .base import ProviderConfigError
from .ollama_native import OllamaNativeProvider
from .resolve import provider_for


ProbeState = Literal["ok", "unreachable", "not-configured", "unauthorized"]


@dataclass(frozen=True)
class ProbeResult:
    state: ProbeState
    detail: str
    latency_ms: float


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)


def _request_for(settings: dict[str, Any]) -> Request:
    provider = provider_for(settings)
    headers: dict[str, str] = {}
    if isinstance(provider, OllamaNativeProvider):
        endpoint = provider.endpoint
        if endpoint.endswith("/api/chat"):
            endpoint = endpoint[: -len("/api/chat")]
        url = endpoint.rstrip("/") + "/api/tags"
    else:
        url = main_chat_url(settings).removesuffix("/chat/completions") + "/models"
        api_key = str(settings.get("api_key") or "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    return Request(url, headers=headers, method="GET")


def _open(request: Request, timeout: float):
    hostname = (urlparse(request.full_url).hostname or "").lower()
    if hostname in {"127.0.0.1", "localhost", "::1"}:
        network_timeout = max(0.001, timeout * 0.9)
        return build_opener(ProxyHandler({})).open(request, timeout=network_timeout)
    return urlopen(request, timeout=timeout)


def probe(settings: dict[str, Any], timeout: float = 5.0) -> ProbeResult:
    endpoint = str(settings.get("endpoint") or "").strip()
    if not settings.get("enabled") or not endpoint:
        return ProbeResult(
            state="not-configured",
            detail="S-MAIN is disabled or has no endpoint",
            latency_ms=0,
        )

    started = perf_counter()
    try:
        request = _request_for(settings)
        with _open(request, timeout=timeout) as response:
            response.read()
        return ProbeResult(state="ok", detail="provider model listing is reachable", latency_ms=_elapsed_ms(started))
    except ProviderConfigError as exc:
        return ProbeResult(state="not-configured", detail=str(exc), latency_ms=_elapsed_ms(started))
    except HTTPError as exc:
        if exc.code in (401, 403):
            return ProbeResult(
                state="unauthorized",
                detail=f"HTTP {exc.code}: provider rejected credentials",
                latency_ms=_elapsed_ms(started),
            )
        return ProbeResult(
            state="unreachable",
            detail=f"HTTP {exc.code}: {exc.reason}",
            latency_ms=_elapsed_ms(started),
        )
    except Exception as exc:
        return ProbeResult(
            state="unreachable",
            detail=f"{type(exc).__name__}: {exc}",
            latency_ms=_elapsed_ms(started),
        )


__all__ = ["ProbeResult", "ProbeState", "probe"]
