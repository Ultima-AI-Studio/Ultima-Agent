"""L9 偏好最小记忆语义层（P2 #63）。

对齐 product-plan v2.3「L9 记忆：偏好最小记忆（偏好/汇报风格记忆），
完整自学习后置」与 data-model「长期事实 Memory：用户事实/偏好/设备/
环境档案引用」：
- 语义层构建在 Mem0Backend（M3 已接）之上，不引入新依赖；
- 偏好条目结构化：scope（个人/汇报/设备/征询）+ key + value + 来源 +
  优先级 + 时间戳；
- 幂等 upsert（同 scope+key 覆盖，append-only 审计留痕）；
- 检索：精确（scope+key 定向）与语义（走 Mem0Backend.retrieve）；
- 写域：H:\\UltimaAI\\UltimaAgent\\data\\memory\\preferences\\。

本文件位于 H:\\UltimaAI\\UltimaAgent\\ 写域内，只写本目录。
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# 合法 scope（对齐 data-model：个人/汇报/设备/征询）
VALID_SCOPES = ("personal", "report", "device", "inquiry")

# 默认偏好数据目录（相对 UltimaAgent 数据根）
_DEFAULT_PREF_DIR = os.path.join(
    os.environ.get("ULTIMA_AGENT_DATA", r"H:\UltimaAI\UltimaAgent\data"),
    "memory",
    "preferences",
)

_KEY_RE = re.compile(r"^[a-z][a-z0-9_.\-]{0,63}$")


@dataclass
class PreferenceEntry:
    """一条结构化偏好。"""

    scope: str
    key: str
    value: Any
    source: str = ""                  # 来源（如 user / task-queue / device-scan）
    priority: int = 0                 # 0=默认，越大越优先
    created_at: str = ""              # ISO8601（UTC）
    updated_at: str = ""              # ISO8601（UTC）

    def to_dict(self) -> dict:
        return asdict(self)


class PreferenceStore:
    """偏好最小记忆语义层。

    Parameters
    ----------
    data_dir:
        持久化目录（JSON 行式 append-only 审计 + 当前态索引）。
    backend:
        可选：Mem0Backend 实例，用于语义检索（无则仅精确检索）。
    """

    def __init__(
        self,
        data_dir: Optional[str] = None,
        *,
        backend: Any = None,
    ) -> None:
        self._data_dir = Path(data_dir or _DEFAULT_PREF_DIR)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._backend = backend
        self._audit_log = self._data_dir / "preferences.jsonl"
        self._index_file = self._data_dir / "index.json"
        self._index: Dict[str, Dict[str, PreferenceEntry]] = {
            "personal": {},
            "report": {},
            "device": {},
            "inquiry": {},
        }
        self._load_index()

    # ------------------------------------------------------------------
    # 写入
    # ------------------------------------------------------------------
    def set(
        self,
        scope: str,
        key: str,
        value: Any,
        *,
        source: str = "user",
        priority: int = 0,
    ) -> PreferenceEntry:
        """写入/覆盖一条偏好（幂等 upsert）。

        scope 非法 / key 非法 → ValueError；value 必须 JSON 可序列化。
        """
        if scope not in VALID_SCOPES:
            raise ValueError(
                f"scope 必须是 {VALID_SCOPES} 之一，got {scope!r}"
            )
        if not _KEY_RE.match(key):
            raise ValueError(
                f"key 必须匹配 {_KEY_RE.pattern!r}，got {key!r}"
            )
        try:
            json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"value 必须 JSON 可序列化：{exc}") from None

        now = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        existing = self._index[scope].get(key)
        entry = PreferenceEntry(
            scope=scope,
            key=key,
            value=value,
            source=source,
            priority=priority,
            created_at=existing.created_at if existing else now,
            updated_at=now,
        )
        self._index[scope][key] = entry

        # append-only 审计留痕
        record = dict(entry.to_dict())
        record["event"] = "upsert"
        with open(self._audit_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._save_index()
        return entry

    # ------------------------------------------------------------------
    # 读取（精确 + 语义）
    # ------------------------------------------------------------------
    def get(self, scope: str, key: str) -> Optional[PreferenceEntry]:
        """精确读取一条偏好（无则 None）。"""
        if scope not in VALID_SCOPES:
            return None
        return self._index[scope].get(key)

    def get_value(self, scope: str, key: str, default: Any = None) -> Any:
        entry = self.get(scope, key)
        return entry.value if entry else default

    def list_scope(self, scope: str) -> List[PreferenceEntry]:
        """列出某 scope 全部偏好（按 key 排序）。"""
        if scope not in VALID_SCOPES:
            return []
        return sorted(self._index[scope].values(), key=lambda e: e.key)

    def all(self) -> List[PreferenceEntry]:
        """列出全部偏好（scope→key 稳定序）。"""
        out: List[PreferenceEntry] = []
        for scope in VALID_SCOPES:
            out.extend(self.list_scope(scope))
        return out

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        scopes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """语义检索偏好（走 backend.retrieve；backend 缺失时回退子串匹配）。

        Returns
        -------
        list[dict]
            每条 {entry: PreferenceEntry.to_dict(), score: float, source: str}
        """
        target_scopes = scopes or list(VALID_SCOPES)
        if self._backend is not None:
            results = self._backend.retrieve(query, top_k=top_k)
            out: List[Dict[str, Any]] = []
            for r in results:
                meta = r.metadata or {}
                scope = meta.get("scope", "")
                if scope in target_scopes:
                    out.append(
                        {
                            "entry": self.get(scope, meta.get("key", "")) or
                            PreferenceEntry(
                                scope=scope, key=meta.get("key", ""),
                                value=r.content, source=meta.get("source", ""),
                            ).to_dict(),
                            "score": float(r.score),
                            "source": "mem0",
                        }
                    )
            return out[:top_k]
        # 回退：子串匹配（不区分大小写）
        q = query.lower()
        out = []
        for scope in target_scopes:
            for e in self._index[scope].values():
                hay = json.dumps(e.to_dict(), ensure_ascii=False).lower()
                if q in hay:
                    out.append(
                        {
                            "entry": e.to_dict(),
                            "score": 0.5,
                            "source": "substring-fallback",
                        }
                    )
        return out[:top_k]

    # ------------------------------------------------------------------
    # 删除 / 清空
    # ------------------------------------------------------------------
    def delete(self, scope: str, key: str) -> bool:
        """删除一条偏好（append-only 留痕 delete 事件）。"""
        if scope not in VALID_SCOPES or key not in self._index[scope]:
            return False
        entry = self._index[scope].pop(key)
        record = dict(entry.to_dict())
        record["event"] = "delete"
        with open(self._audit_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._save_index()
        return True

    def clear(self) -> int:
        """清空全部偏好（留痕 clear 事件）。返回删除条数。"""
        entries = self.all()
        record = {
            "event": "clear",
            "count": len(entries),
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        with open(self._audit_log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._index = {s: {} for s in VALID_SCOPES}
        self._save_index()
        return len(entries)

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------
    def _load_index(self) -> None:
        if not self._index_file.exists():
            return
        try:
            raw = json.loads(self._index_file.read_text(encoding="utf-8"))
            for scope in VALID_SCOPES:
                for key, item in (raw.get(scope) or {}).items():
                    self._index[scope][key] = PreferenceEntry(**item)
        except (json.JSONDecodeError, TypeError) as exc:
            # 索引损坏：不阻断（内存态继续，下次写入覆盖）
            self._index = {s: {} for s in VALID_SCOPES}
            self._index_file.rename(self._index_file.with_suffix(".corrupt.json"))

    def _save_index(self) -> None:
        payload = {
            scope: {k: v.to_dict() for k, v in self._index[scope].items()}
            for scope in VALID_SCOPES
        }
        self._index_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ------------------------------------------------------------------
    # 快照（供审计 / Console）
    # ------------------------------------------------------------------
    def snapshot(self) -> dict:
        return {
            "data_dir": str(self._data_dir),
            "total": len(self.all()),
            "by_scope": {s: len(self._index[s]) for s in VALID_SCOPES},
            "audit_log": str(self._audit_log),
            "backend": self._backend is not None,
        }


__all__ = ["PreferenceStore", "PreferenceEntry", "VALID_SCOPES"]
