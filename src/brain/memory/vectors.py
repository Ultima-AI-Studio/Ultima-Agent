"""本地向量检索（s3-memory-base · ACCEPT-2）。

主选：onnx 嵌入（fastembed ONNXMiniLM），离线自研轻量；
备选：Mem0 语义增强（既有 Mem0Backend），PoC 结论落档
（数据目录 data/memory/onnx-poc-result.json，探测与降级全记录）。

向量层将条目编码为向量，检索时按余弦相似度排序；向量不可用时
回退 MemoryLayers.read 关键词检索（不中断功能）。
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from .layers import MemoryEntry, MemoryLayers

_DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"  # 中文场景轻量 onnx（fastembed 官方支持，512 维）
_POC_RESULT_NAME = "onnx-poc-result.json"


class OnnxEmbeddingProbe:
    """PoC 探测：fastembed/onnxruntime 是否可用、能否加载模型。结论落档。"""

    def __init__(self, data_dir: str | Path, model: str = _DEFAULT_MODEL) -> None:
        self.data_dir = Path(data_dir)
        self.model = model
        self.result_path = self.data_dir / _POC_RESULT_NAME

    def probe(self) -> dict[str, Any]:
        started = time.time()
        result: dict[str, Any] = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        try:
            from fastembed import TextEmbedding  # type: ignore
            emb = TextEmbedding(model_name=self.model)
            vec = emb.embed(["ultima memory probe"])
            dims = len(next(iter(vec)))
            result.update({
                "ok": True,
                "backend": "fastembed-onnx",
                "model": self.model,
                "dims": int(dims),
                "latency_ms": round((time.time() - started) * 1000, 1),
                "fallback": None,
            })
        except Exception as exc:  # noqa: BLE001 - PoC 探测捕获全部失败并落档
            result.update({
                "ok": False,
                "backend": None,
                "model": self.model,
                "dims": None,
                "latency_ms": round((time.time() - started) * 1000, 1),
                "error": str(exc)[:300],
                "fallback": "ollama-nomic-embed-text（既有 Mem0Backend 通道）",
            })
        self.result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result


class VectorRetriever:
    """向量检索器：onnx 主选 → 无向量回退关键词。"""

    def __init__(
        self,
        layers: MemoryLayers,
        data_dir: str | Path,
        model: str = _DEFAULT_MODEL,
    ) -> None:
        self._layers = layers
        self._data_dir = Path(data_dir)
        self._model = model
        self._embedder = None
        self._cache: dict[str, list[float]] = {}

    def _get_embedder(self):
        if self._embedder is None:
            from fastembed import TextEmbedding  # type: ignore
            self._embedder = TextEmbedding(model_name=self._model)
        return self._embedder

    def embed(self, text: str) -> list[float]:
        key = text
        if key in self._cache:
            return self._cache[key]
        emb = self._get_embedder()
        vec = next(iter(emb.embed([text])))
        out = [float(x) for x in vec]
        self._cache[key] = out
        return out

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = sum(x * x for x in a) ** 0.5
        nb = sum(y * y for y in b) ** 0.5
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def search(
        self,
        query: str,
        *,
        layer: str | None = None,
        top_k: int = 5,
        include_cold: bool = False,
    ) -> list[tuple[MemoryEntry, float]]:
        """向量检索（s7：支持冷档回退——温档无命中且开启冷档检索时解冻参与评分）。"""
        try:
            qvec = self.embed(query)
        except Exception:
            # 向量不可用：回退关键词检索（不中断）；冷档条目一并参与
            entries = self._layers.read(query, layer=layer, top_k=top_k, include_cold=include_cold)
            return [(e, 0.0) for e in entries]
        targets = (layer,) if layer else (
            "declarative", "procedural", "device_profile", "env_profile"
        )
        scored: list[tuple[MemoryEntry, float]] = []
        for ly in targets:
            for entry in self._layers.read("", layer=ly, top_k=1000000):
                if entry.deleted:
                    continue
                try:
                    score = self._cosine(qvec, self.embed(f"{entry.content} {entry.source}"))
                except Exception:
                    score = 0.0
                scored.append((entry, score))
        if include_cold:
            # 冷档回退：温档无命中时解冻归档条目参与评分；命中后回写温档（thaw）
            hot_warm_ids = {e.id for _, e in scored}
            cold_hits: list[tuple[MemoryEntry, float]] = []
            for ly in targets:
                for entry in self._layers.read_archived(ly):
                    if entry.id in hot_warm_ids or entry.deleted:
                        continue
                    try:
                        score = self._cosine(qvec, self.embed(f"{entry.content} {entry.source}"))
                    except Exception:
                        score = 0.0
                    cold_hits.append((entry, score))
            if cold_hits and not scored:
                # 仅当温档零命中时启用冷档结果，且命中即解冻回温
                cold_hits.sort(key=lambda x: x[1], reverse=True)
                for entry, _score in cold_hits[:top_k]:
                    self._layers.thaw_cold(entry.id)
                return cold_hits[:top_k]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]


__all__ = ["VectorRetriever", "OnnxEmbeddingProbe"]
