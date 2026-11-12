"""L9 记忆拼装层（M3 + P2 #63）。

接线范式（对齐 tech-progression-plan §2）：
1. 接口对齐：实现 openjarvis.tools.storage._stubs.MemoryBackend
   （store / retrieve / delete）
2. 注册接入：MemoryRegistry.register("mem0") 注册进底座 registry
3. 数据分层：user / session / agent 三层，对齐 data-model
4. 锁版本：mem0ai 2.2.1 + qdrant/faiss 依赖锁 wheels
5. 偏好最小记忆（P2 #63）：PreferenceStore 语义层构建在 Mem0Backend
   之上，结构化 scope/key/value + append-only 审计

本层是 UltimaAgent 自研适配：以 mem0ai 为底层引擎（ollama embed +
本地向量存储），对外暴露底座 MemoryBackend 契约，供 Jarvis 记忆原语调用。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from .backend import Mem0Backend, RetrievalResult
from .preference import PreferenceEntry, PreferenceStore
from .registry import MemoryRegistry, ResidencyViolationError
from .layers import MemoryLayers, MemoryEntry, MemoryLayerError, LAYERS, KINDS
from .gate import MemoryWriteGate, GateDecision, TRUSTED_SOURCES, UNTRUSTED_SOURCES
from .reflection import ReflectionWriter, Reflection, forgetting_rules
from .vectors import VectorRetriever, OnnxEmbeddingProbe

__all__ = [
    "Mem0Backend",
    "RetrievalResult",
    "PreferenceEntry",
    "PreferenceStore",
    "MemoryRegistry",
    "ResidencyViolationError",
    "MemoryLayers",
    "MemoryEntry",
    "MemoryLayerError",
    "LAYERS",
    "KINDS",
    "MemoryWriteGate",
    "GateDecision",
    "TRUSTED_SOURCES",
    "UNTRUSTED_SOURCES",
    "ReflectionWriter",
    "Reflection",
    "forgetting_rules",
    "VectorRetriever",
    "OnnxEmbeddingProbe",
]
