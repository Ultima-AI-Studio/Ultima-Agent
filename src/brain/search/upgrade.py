"""检索增强（s3-websearch-upgrade · M14）。

对齐 agent-capability-notes §⑥ 检索增强要求：
1. 多引擎编排：primary → fallback 链式降级；
2. 来源标记：每条结果带来源 URL/引擎/时效，可追溯；
3. 降级标记：发生降级时整体标记 degraded + 原因；
4. SSRF 防护：解析目标 URL 主机为内网/回环/云元数据地址（169.254.169.254 等）一律拒绝。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import ipaddress
import json
import socket
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    engine: str
    fetched_at: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"title": self.title, "url": self.url, "snippet": self.snippet,
                "engine": self.engine, "fetched_at": self.fetched_at}


class SSRFGuard:
    """SSRF 防护：内网/回环/元数据地址拒绝（DNS 解析后判定）。"""

    PRIVATE_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2",
                        "192.168.", "127.", "169.254.", "0.", "100.64.", "100.65.")

    def validate(self, url: str) -> tuple[bool, str]:
        """校验目标 URL 主机；拒绝内网/回环/云元数据。"""
        try:
            from urllib.parse import urlparse

            host = urlparse(url).netloc
            if not host:
                return False, "URL 无主机"
            # 去掉端口与 userinfo
            host = host.rsplit("@", 1)[-1].split(":", 1)[0].strip("[]")
            if host in ("localhost", "metadata.google.internal"):
                return False, f"SSRF：{host} 属内网/元数据地址"
            # 字面 IP
            try:
                ip = ipaddress.ip_address(host)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return False, f"SSRF：{host} 属内网/保留地址"
            except ValueError:
                pass
            # DNS 解析（仅首条 A 记录，控制超时）
            try:
                for addr in socket.getaddrinfo(host, None):
                    ip_str = addr[4][0]
                    try:
                        ip = ipaddress.ip_address(ip_str)
                    except ValueError:
                        continue
                    if ip.is_private or ip.is_loopback or ip.is_link_local:
                        return False, f"SSRF：{host} 解析到内网 {ip_str}"
            except socket.gaierror:
                return False, f"域名无法解析 {host}"
        except Exception as exc:  # noqa: BLE001
            return False, f"SSRF 校验异常 {exc}"
        return True, "允许"


class SearchOrchestrator:
    """多引擎编排：primary → fallback，来源标记 + 降级标记。"""

    def __init__(self, engines: Optional[dict[str, Callable[[str], list[dict[str, Any]]]]] = None) -> None:
        # 引擎签名：(query) -> [{title,url,snippet}]
        self.engines: dict[str, Callable[[str], list[dict[str, Any]]]] = engines or {}
        self.guard = SSRFGuard()
        self._history: list[dict[str, Any]] = []

    def register(self, name: str, fn: Callable[[str], list[dict[str, Any]]]) -> None:
        self.engines[name] = fn

    def search(self, query: str, *, engine_order: Optional[list[str]] = None) -> dict[str, Any]:
        order = engine_order or list(self.engines.keys())
        degraded = False
        used_engine = ""
        last_err = ""
        blocked = 0
        for name in order:
            fn = self.engines.get(name)
            if fn is None:
                continue
            try:
                raw = fn(query) or []
            except Exception as exc:  # noqa: BLE001
                last_err = f"{name} 失败：{exc}"
                degraded = True
                continue
            results: list[SearchResult] = []
            for item in raw:
                url = item.get("url", "")
                ok, _ = self.guard.validate(url)
                if not ok:
                    blocked += 1
                    continue
                results.append(SearchResult(
                    title=item.get("title", ""), url=url,
                    snippet=item.get("snippet", ""), engine=name,
                ))
            if results:
                used_engine = name
                break
            degraded = True
            last_err = f"{name} 无结果"
        out = {
            "query": query,
            "results": [r.as_dict() for r in results] if used_engine else [],
            "engine": used_engine,
            "degraded": degraded,
            "degraded_reason": last_err if degraded else "",
            "blocked_count": blocked,
            "ts": _now_iso(),
        }
        self._history.append(out)
        return out


__all__ = ["SearchOrchestrator", "SSRFGuard", "SearchResult"]
