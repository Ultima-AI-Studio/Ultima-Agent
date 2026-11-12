"""四层记忆结构（s3-memory-base · M17 分层记忆底座）+ 热度轴（s7-memory-temperature）。

对齐 ADR-008 冻结基线 + data-model.md + memory-temperature-tiering-20261027.md：
- 工作记忆 working：会话级短期上下文（可含未核验暂存，闸门管控）
- 声明式 declarative：长期事实（用户事实/偏好/档案引用，只入可信）
- 程序式 procedural：流程/技能/反思条目
- 设备档案 device_profile / 环境档案 env_profile：对齐 device-cluster 五项与环境快照

热度轴（s7 增量，不推翻冻结基线）：
- 三档 temperature：hot（热，内存常驻即时召回）/ warm（温，磁盘快速索引）/ cold（冷，gz 归档按需解冻）
- 升降级四动作：promote_hot / demote_warm / archive_cold / thaw_cold
- 时间三层映射：短期=working+打断单元（热）；中期=declarative 温档活跃条目（不新增存储文件）；长期=declarative/procedural 常规（温→冷）
- 打断单元 kind=pending_interrupt（working 层，默认热档）

存储：data/memory/layers/<layer>.jsonl 追加式；冷归档 data/memory/archive/<layer>.jsonl.gz；
每条带 id/ts/layer/kind/content/trusted/source/meta；删除=软删（deleted=True 保留行，可回溯）；
遗忘按 max_entries/retention_days 逐出并留驱逐审计。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import gzip
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

LAYERS = (
    "working",
    "declarative",
    "procedural",
    "device_profile",
    "env_profile",
)
KINDS = ("fact", "suggestion", "reflection", "profile", "pending", "pending_interrupt")

DEFAULT_MAX_ENTRIES = {"working": 200, "declarative": 500, "procedural": 300,
                       "device_profile": 100, "env_profile": 100}
DEFAULT_RETENTION_DAYS = {"working": 1, "declarative": 365, "procedural": 730,
                          "device_profile": 365, "env_profile": 365}

# 热度轴默认档（s7）：working=hot、env_profile=cold、其余=warm
DEFAULT_TEMPERATURE = {"working": "hot", "declarative": "warm", "procedural": "warm",
                       "device_profile": "warm", "env_profile": "cold"}
# 热档判定阈值：会话内召回 ≥ HOT_TOUCH_THRESHOLD 次即升热
HOT_TOUCH_THRESHOLD = 2
# 冷档判定：超过保留期 或 30 天未被召回 且判定低价值
COLD_STALE_DAYS = 30
ARCHIVE_DIR_NAME = "archive"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _is_iso_newer(a: str, b: str) -> bool:
    return a > b


@dataclass
class MemoryEntry:
    id: str
    ts: str
    layer: str
    kind: str
    content: str
    trusted: bool
    source: str
    meta: dict[str, Any] = field(default_factory=dict)
    deleted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "ts": self.ts, "layer": self.layer, "kind": self.kind,
            "content": self.content, "trusted": self.trusted, "source": self.source,
            "meta": self.meta, "deleted": self.deleted,
        }

    # -- 热度轴便捷属性（s7） ------------------------------------------------
    @property
    def temperature(self) -> str:
        return str(self.meta.get("temperature", "warm"))

    def set_temperature(self, value: str, *, persist: bool = False) -> None:
        if value not in ("hot", "warm", "cold"):
            raise MemoryLayerError(f"未知热度档: {value}（可选 hot/warm/cold）")
        self.meta["temperature"] = value


class MemoryLayerError(Exception):
    """记忆层操作失败。"""


class MemoryLayers:
    """四层记忆：写入/检索/回溯/删除/遗忘边界 + 热度轴（s7）。"""

    def __init__(
        self,
        data_dir: str | Path,
        max_entries: Optional[dict[str, int]] = None,
        retention_days: Optional[dict[str, int]] = None,
        hot_touch_threshold: int = HOT_TOUCH_THRESHOLD,
        cold_stale_days: int = COLD_STALE_DAYS,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.layers_dir = self.data_dir / "layers"
        self.archive_dir = self.data_dir / ARCHIVE_DIR_NAME
        self.layers_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.max_entries = {**DEFAULT_MAX_ENTRIES, **(max_entries or {})}
        self.retention_days = {**DEFAULT_RETENTION_DAYS, **(retention_days or {})}
        self.hot_touch_threshold = int(hot_touch_threshold)
        self.cold_stale_days = int(cold_stale_days)
        self._index: dict[str, dict[str, MemoryEntry]] = {layer: {} for layer in LAYERS}
        self._load()

    # -- 加载与持久化 -------------------------------------------------------

    def _path(self, layer: str) -> Path:
        if layer not in LAYERS:
            raise MemoryLayerError(f"未知层: {layer}（可选 {LAYERS}）")
        return self.layers_dir / f"{layer}.jsonl"

    def _load(self) -> None:
        for layer in LAYERS:
            p = self._path(layer)
            if not p.exists():
                continue
            for line in p.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                    self._index[layer][obj["id"]] = MemoryEntry(**{
                        k: v for k, v in obj.items()
                        if k in MemoryEntry.__dataclass_fields__
                    })
                except (json.JSONDecodeError, KeyError):
                    continue

    def _append(self, entry: MemoryEntry) -> None:
        with self._path(entry.layer).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry.as_dict(), ensure_ascii=False) + "\n")
            fh.flush()

    # -- 写入 ---------------------------------------------------------------

    def write(
        self,
        layer: str,
        content: str,
        *,
        kind: str = "fact",
        trusted: bool = True,
        source: str = "system",
        meta: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        if layer not in LAYERS:
            raise MemoryLayerError(f"未知层: {layer}")
        if kind not in KINDS:
            raise MemoryLayerError(f"未知 kind: {kind}（可选 {KINDS}）")
        if not content or not str(content).strip():
            raise MemoryLayerError("内容不能为空")
        meta = dict(meta or {})
        # 热度轴默认档（s7）：按层默认 temperature，写入即打标
        meta.setdefault("temperature", DEFAULT_TEMPERATURE.get(layer, "warm"))
        meta.setdefault("access_count", 0)
        meta.setdefault("last_access", "")
        entry = MemoryEntry(
            id=uuid.uuid4().hex[:16],
            ts=_now_iso(),
            layer=layer,
            kind=kind,
            content=str(content),
            trusted=bool(trusted),
            source=source,
            meta=meta,
        )
        self._index[layer][entry.id] = entry
        self._append(entry)
        self._enforce_boundary(layer, keep_id=entry.id)
        return entry

    # -- 检索 ---------------------------------------------------------------

    def read(
        self,
        query: str,
        *,
        layer: str | None = None,
        top_k: int = 5,
        kinds: Optional[tuple[str, ...]] = None,
        session: Optional[str] = None,
        include_cold: bool = False,
    ) -> list[MemoryEntry]:
        """检索：命中即 touch（召回计数，s7 热度轴）。

        三级路由：热（内存索引，默认已含 hot/warm 档）→ 温（磁盘 jsonl）→
        冷（仅 include_cold=True 时解冻归档条目参与）。命中即停，降级不丢。
        冷档命中条目不 touch（归档条目不在内存索引，计数语义不适用）。
        """
        needle = str(query).strip().casefold()
        hits: list[MemoryEntry] = []
        targets = (layer,) if layer else LAYERS
        for ly in targets:
            for entry in self._index[ly].values():
                if entry.deleted or entry.meta.get("archived"):
                    continue
                if kinds and entry.kind not in kinds:
                    continue
                hay = f"{entry.content} {entry.source} {json.dumps(entry.meta, ensure_ascii=False)}".casefold()
                if not needle:
                    hits.append(entry)
                elif needle in hay:
                    hits.append(entry)
        if include_cold:
            for ly in targets:
                for entry in self.read_archived(ly, query, kinds=kinds):
                    hits.append(entry)
        hits.sort(key=lambda e: e.ts, reverse=True)
        top = hits[:top_k]
        for entry in top:
            self.touch(entry.id, session=session)
        return top

    def read_archived(
        self,
        layer: str,
        query: str = "",
        *,
        top_k: int = 0,
        kinds: Optional[tuple[str, ...]] = None,
    ) -> list[MemoryEntry]:
        """只读冷归档（s7）：不带 touch 语义，供检索/解冻调用。"""
        needle = str(query).strip().casefold()
        out: list[MemoryEntry] = []
        for entry in self._read_archived(layer):
            if entry.deleted:
                continue
            if kinds and entry.kind not in kinds:
                continue
            hay = f"{entry.content} {entry.source}".casefold()
            if not needle or needle in hay:
                out.append(entry)
        out.sort(key=lambda e: e.ts, reverse=True)
        if top_k > 0:
            out = out[:top_k]
        return out

    def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        for layer in LAYERS:
            if entry_id in self._index[layer]:
                return self._index[layer][entry_id]
        return None

    # -- 热度轴（s7）：touch / 升降级 / 冷归档 --------------------------------

    def touch(self, entry_id: str, *, session: Optional[str] = None) -> bool:
        """召回计数：access_count+1、更新 last_access；会话内 ≥2 次升热（内存标记）。

        冷档条目（archived）不计数——需先解冻回温。
        """
        entry = self.get_by_id(entry_id)
        if entry is None or entry.deleted or entry.meta.get("archived"):
            return False
        entry.meta["access_count"] = int(entry.meta.get("access_count", 0)) + 1
        entry.meta["last_access"] = _now_iso()
        if session:
            entry.meta.setdefault("last_session", session)
            if entry.meta.get("last_session") == session and \
                    int(entry.meta.get("access_count", 0)) >= self.hot_touch_threshold:
                entry.set_temperature("hot")  # 热=内存标记，不落盘（运行时态）
        return True

    def promote_hot(self, entry_id: str) -> bool:
        """升热：内存标记 hot（不落盘）。冷档条目先解冻。"""
        entry = self.get_by_id(entry_id)
        if entry is None or entry.deleted or entry.meta.get("archived"):
            return False
        entry.set_temperature("hot")
        return True

    def demote_warm(self, entry_id: str) -> bool:
        """降温：置 warm 并落盘。冷档条目先解冻。"""
        entry = self.get_by_id(entry_id)
        if entry is None or entry.deleted or entry.meta.get("archived"):
            return False
        entry.set_temperature("warm")
        self._rewrite_layer(entry.layer)
        return True

    def demote_all_hot(self, layer: str) -> int:
        """批量降热（s7 会话收尾）：该层所有 hot 条目置 warm，一次落盘。"""
        if layer not in LAYERS:
            return 0
        changed = 0
        for entry in self._index[layer].values():
            if entry.deleted:
                continue
            if entry.temperature == "hot":
                entry.set_temperature("warm")
                changed += 1
        if changed:
            self._rewrite_layer(layer)
        return changed

    def archive_cold(self, entry_id: str) -> bool:
        """降冷：追加进 archive gz，原行 meta.archived=True 标记不删行，可回溯。"""
        entry = self.get_by_id(entry_id)
        if entry is None or entry.deleted:
            return False
        entry.set_temperature("cold")
        entry.meta["archived"] = True
        entry.meta["archived_at"] = _now_iso()
        self._append_archive(entry)
        self._rewrite_layer(entry.layer)
        return True

    def thaw_cold(self, entry_id: str) -> bool:
        """解冻：冷归档条目回写温档 jsonl 并置 warm；返回是否成功。"""
        for layer in LAYERS:
            for entry in self._read_archived(layer):
                if entry.id != entry_id:
                    continue
                entry.set_temperature("warm")
                entry.meta["archived"] = False
                entry.meta.pop("archived_at", None)
                entry.meta["thawed_at"] = _now_iso()
                self._index[layer][entry.id] = entry
                self._append(entry)
                self._remove_from_archive(layer, entry_id)
                return True
        return False

    def stale_candidates(self) -> list[MemoryEntry]:
        """冷档候选：超保留期 或 30 天未召回（cold_stale_days）的未删除条目。"""
        now = datetime.now(timezone.utc)
        out: list[MemoryEntry] = []
        for layer in LAYERS:
            for entry in self._index[layer].values():
                if entry.deleted or entry.meta.get("archived"):
                    continue
                stale = False
                try:
                    ts = datetime.fromisoformat(entry.ts.replace("Z", "+00:00"))
                    if now - ts > timedelta(days=self.retention_days[layer]):
                        stale = True
                except ValueError:
                    pass
                last = entry.meta.get("last_access", "")
                if last:
                    try:
                        last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                        if now - last_dt > timedelta(days=self.cold_stale_days):
                            stale = True
                    except ValueError:
                        pass
                if stale:
                    out.append(entry)
        return out

    # -- 冷归档读写（标准库 gzip） -------------------------------------------

    def _archive_path(self, layer: str) -> Path:
        return self.archive_dir / f"{layer}.jsonl.gz"

    def _append_archive(self, entry: MemoryEntry) -> None:
        p = self._archive_path(entry.layer)
        payload = (json.dumps(entry.as_dict(), ensure_ascii=False) + "\n").encode("utf-8")
        with gzip.open(p, "ab") as fh:
            fh.write(payload)

    def _read_archived(self, layer: str) -> list[MemoryEntry]:
        p = self._archive_path(layer)
        if not p.exists():
            return []
        out: list[MemoryEntry] = []
        try:
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                        out.append(MemoryEntry(**{
                            k: v for k, v in obj.items()
                            if k in MemoryEntry.__dataclass_fields__
                        }))
                    except (json.JSONDecodeError, KeyError):
                        continue
        except (OSError, EOFError):
            return []
        return out

    def _remove_from_archive(self, layer: str, entry_id: str) -> None:
        """从归档 gz 移除已解冻条目：读全量 → 过滤 → 重写 gz。"""
        p = self._archive_path(layer)
        if not p.exists():
            return
        rows = [e for e in self._read_archived(layer) if e.id != entry_id]
        with gzip.open(p, "wt", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row.as_dict(), ensure_ascii=False) + "\n")

    # -- 删除（软删可回溯） -------------------------------------------------

    def delete(self, entry_id: str) -> bool:
        for layer in LAYERS:
            entry = self._index[layer].get(entry_id)
            if entry is not None:
                entry.deleted = True
                entry.meta["deleted_at"] = _now_iso()
                self._rewrite_layer(layer)
                return True
        return False

    def _rewrite_layer(self, layer: str) -> None:
        # 软删不删行：重写该层文件保留全部历史（追加式语义，可回溯）
        rows = [self._index[layer][eid].as_dict() for eid in sorted(self._index[layer])]
        with self._path(layer).open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()

    # -- 遗忘边界 -----------------------------------------------------------

    def _enforce_boundary(self, layer: str, keep_id: str) -> None:
        entries = [e for e in self._index[layer].values() if not e.deleted]
        if len(entries) <= self.max_entries[layer]:
            return
        # 超出：按时间逐出最旧条目（LRU），保留 keep_id
        ordered = sorted(entries, key=lambda e: e.ts)
        evicted: list[MemoryEntry] = []
        for old in ordered:
            if len([e for e in self._index[layer].values() if not e.deleted]) <= self.max_entries[layer]:
                break
            if old.id == keep_id:
                continue
            old.deleted = True
            old.meta["evicted"] = True
            old.meta["evicted_at"] = _now_iso()
            evicted.append(old)
        if evicted:
            self._rewrite_layer(layer)
            self._log_eviction(layer, evicted)

    def forget_expired(self) -> int:
        """按 retention_days 逐出过期条目，返回驱逐数。"""
        now = datetime.now(timezone.utc)
        total = 0
        for layer in LAYERS:
            expired = [
                e for e in self._index[layer].values()
                if not e.deleted and not e.meta.get("evicted")
            ]
            to_evict: list[MemoryEntry] = []
            for e in expired:
                try:
                    ts = datetime.fromisoformat(e.ts.replace("Z", "+00:00"))
                except ValueError:
                    continue
                if now - ts > timedelta(days=self.retention_days[layer]):
                    to_evict.append(e)
            if to_evict:
                for e in to_evict:
                    e.deleted = True
                    e.meta["evicted"] = True
                    e.meta["evicted_at"] = _now_iso()
                self._rewrite_layer(layer)
                self._log_eviction(layer, to_evict)
                total += len(to_evict)
        return total

    def _log_eviction(self, layer: str, entries: list[MemoryEntry]) -> None:
        log_path = self.data_dir / "logs" / "memory-evictions.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fh:
            for e in entries:
                fh.write(json.dumps({
                    "ts": _now_iso(), "layer": layer, "id": e.id,
                    "reason": "evicted", "content_preview": e.content[:80],
                }, ensure_ascii=False) + "\n")
            fh.flush()

    # -- 统计 ---------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        out = {}
        for layer in LAYERS:
            entries = list(self._index[layer].values())
            out[layer] = {
                "total": len(entries),
                "active": sum(1 for e in entries if not e.deleted),
                "deleted": sum(1 for e in entries if e.deleted),
            }
        return out


__all__ = ["MemoryLayers", "MemoryEntry", "MemoryLayerError", "LAYERS", "KINDS",
           "DEFAULT_TEMPERATURE", "HOT_TOUCH_THRESHOLD", "COLD_STALE_DAYS"]
