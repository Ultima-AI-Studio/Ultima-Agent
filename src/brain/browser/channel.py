"""浏览器自动化通道（s3-browser-channel · M13）。

对齐 OpenClaw/Open Interpreter §⑤（双浏览器策略）+ Agent-Reach 只读红线：
1. 托管浏览器/CDP 双轨接入（导航/观察/元素定位/操作执行接口，白名单站点）；
2. 登录态会话隔离（独立 profile，与用户日常浏览器隔离）；
3. 只读红线：发帖/评论/点赞/私信/代登录/索要密码 → 闸门拒绝并留痕；
4. 动作全程审计留痕（append JSONL）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# 只读红线：这些动作一律拒绝
REDLINE_ACTIONS = {
    "post", "comment", "like", "follow", "message", "dm", "send",
    "login", "login_as", "enter_password", "submit_form",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class BrowserChannelError(Exception):
    pass


@dataclass
class AuditEntry:
    action: str
    target: str
    allowed: bool
    reason: str
    ts: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"action": self.action, "target": self.target, "allowed": self.allowed,
                "reason": self.reason, "ts": self.ts}


class RedlineGate:
    """只读红线闸门：动作前判定，拒绝并留痕。"""

    def __init__(self, whitelist_sites: Optional[list[str]] = None) -> None:
        self.whitelist = set(whitelist_sites or [])
        self.events: list[AuditEntry] = []

    def allow(self, action: str, target: str) -> tuple[bool, str]:
        if action in REDLINE_ACTIONS:
            return False, f"只读红线：{action} 属越界动作（发帖/评论/点赞/私信/代登录等一律拒绝）"
        if self.whitelist and target and not any(target.startswith(s) for s in self.whitelist):
            return False, f"站点不在白名单：{target}"
        return True, "允许"

    def record(self, action: str, target: str, allowed: bool, reason: str) -> None:
        self.events.append(AuditEntry(action, target, allowed, reason))

    def audit_log(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            for ev in self.events:
                fh.write(json.dumps(ev.as_dict(), ensure_ascii=False) + "\n")
        self.events.clear()


@dataclass
class PageObservation:
    url: str
    title: str = ""
    elements: list[dict[str, Any]] = field(default_factory=list)
    note: str = ""


class BrowserChannel:
    """托管浏览器/CDP 双轨接口（本地桩 + 动作闸门，真机接 CDP 时替换执行层）。"""

    def __init__(
        self,
        *,
        profile_dir: Optional[str | Path] = None,
        whitelist_sites: Optional[list[str]] = None,
        audit_path: Optional[str | Path] = None,
        search_factory=None,
        fetch_factory=None,
    ) -> None:
        self.profile_dir = Path(profile_dir) if profile_dir else Path("data/browser/profile-isolated")
        self.gate = RedlineGate(whitelist_sites)
        self.audit_path = Path(audit_path) if audit_path else Path("data/browser/audit.jsonl")
        self._sessions: dict[str, dict[str, Any]] = {}
        self._search_factory = search_factory
        self._fetch_factory = fetch_factory

    def search_public(self, query: str, max_results: int = 5) -> dict:
        from openjarvis.tools.web_search import WebSearchTool
        if not isinstance(query,str) or not query.strip() or len(query)>2000 or WebSearchTool._extract_url(query):
            raise ValueError('Search requires text without an HTTP URL; use GET for URLs')
        if type(max_results) is not int or not 1<=max_results<=5:
            raise ValueError('Search result count must be 1..5')
        allowed,reason=self.gate.allow('search','')
        if not allowed: raise ValueError(reason)
        sdk=(self._search_factory or WebSearchTool)(engine='duckduckgo')
        result=sdk.execute(query=query,max_results=max_results)
        if not result.success: raise ValueError(result.content)
        return dict(success=True,engine='duckduckgo',query=query,body=result.content,fetched_at=_now_iso())

    def fetch_public(self, url: str) -> dict:
        import hashlib
        import urllib.parse
        from openjarvis.security.ssrf import check_ssrf
        from openjarvis.tools.http_request import HttpRequestTool
        parts=urllib.parse.urlsplit(url)
        if parts.scheme not in ('http','https') or not parts.hostname or parts.username or parts.password or parts.fragment:
            raise ValueError('Only public HTTP URLs without credentials/fragments are allowed')
        blocked=check_ssrf(url)
        if blocked: raise ValueError(blocked)
        allowed,reason=self.gate.allow('fetch',url)
        if not allowed: raise ValueError(reason)
        class ProvenanceGET(HttpRequestTool):
            def _request_following_redirects(self,*args,**kwargs):
                response=super()._request_following_redirects(*args,**kwargs)
                self.final_url=str(response.url)
                return response
        sdk=(self._fetch_factory or ProvenanceGET)()
        result=sdk.execute(url=url,method='GET',headers={'Accept':'text/html,text/plain,application/json'},timeout=30)
        meta=result.metadata or {}
        status=meta.get('status_code',0)
        kind=meta.get('content_type','').split(';')[0].lower()
        if not result.success or not 200<=status<300 or kind not in ('text/html','text/plain','application/json','application/xhtml+xml') or not result.content.strip():
            raise ValueError('GET failed or unsupported/empty content: HTTP '+str(status)+'; '+(result.content[:500] if not result.success else kind))
        final=getattr(sdk,'final_url',meta.get('final_url',url))
        p=urllib.parse.urlsplit(final)
        if p.scheme not in ('http','https') or p.username or p.password or check_ssrf(final):
            raise ValueError('Invalid final URL')
        from html.parser import HTMLParser
        class Text(HTMLParser):
            def __init__(self): super().__init__(); self.parts=[]; self.skip=0
            def handle_starttag(self,tag,attrs):
                if tag in ('script','style'): self.skip+=1
            def handle_endtag(self,tag):
                if tag in ('script','style'): self.skip=max(0,self.skip-1)
            def handle_data(self,data):
                if not self.skip: self.parts.append(data)
        parser=Text()
        if 'html' in kind: parser.feed(result.content)
        text=' '.join(parser.parts) if 'html' in kind else result.content
        host=p.hostname.lower()
        port=p.port
        netloc=host if port in (None,80 if p.scheme=='http' else 443) else host+':'+str(port)
        normalized=urllib.parse.urlunsplit((p.scheme.lower(),netloc,p.path or '/',p.query,''))
        return dict(success=True,requested_url=url,final_url=final,dedupe_url=normalized,
                    source_id=__import__('uuid').uuid4().hex,
                    fetched_at=_now_iso(),status_code=status,content_type=kind,
                    truncated=bool(meta.get('truncated')),body=result.content,text=text,
                    decoded_body_sha256=hashlib.sha256(result.content.encode('utf-8')).hexdigest())

    # -- 会话隔离 -----------------------------------------------------------

    def new_session(self, session_id: str) -> dict[str, Any]:
        """每个会话独立 profile（隔离登录态，不共享用户日常登录）。"""
        profile = self.profile_dir / f"profile-{session_id}"
        self._sessions[session_id] = {"profile": str(profile), "isolated": True}
        return {"session_id": session_id, "profile": str(profile), "isolated": True}

    # -- 导航/观察/操作（动作前过闸门） ---------------------------------------

    def navigate(self, session_id: str, url: str) -> PageObservation:
        self._require(session_id)
        allowed, reason = self.gate.allow("navigate", url)
        self.gate.record("navigate", url, allowed, reason)
        if not allowed:
            return PageObservation(url=url, note=reason)
        # 真机接入点：CDP Page.navigate；本层返回桩观察
        return PageObservation(url=url, title=f"stub:{url}", elements=[], note="CDP 接入点已预留")

    def observe(self, session_id: str, url: str) -> PageObservation:
        self._require(session_id)
        allowed, reason = self.gate.allow("observe", url)
        self.gate.record("observe", url, allowed, reason)
        if not allowed:
            return PageObservation(url=url, note=reason)
        return PageObservation(url=url, title="observed", note="观察接口（只读）")

    def execute(self, session_id: str, action: str, target: str) -> dict[str, Any]:
        """动作执行：写动作一律红线拒绝。"""
        self._require(session_id)
        allowed, reason = self.gate.allow(action, target)
        self.gate.record(action, target, allowed, reason)
        if not allowed:
            return {"ok": False, "action": action, "target": target, "reason": reason}
        return {"ok": True, "action": action, "target": target, "note": "白名单只读动作执行"}

    def flush_audit(self) -> Path:
        self.gate.audit_log(self.audit_path)
        return self.audit_path

    def _require(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise BrowserChannelError(f"会话不存在 {session_id}")


__all__ = ["BrowserChannel", "RedlineGate", "BrowserChannelError",
           "PageObservation", "REDLINE_ACTIONS"]
