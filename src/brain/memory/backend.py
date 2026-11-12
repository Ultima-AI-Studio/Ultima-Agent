"""Mem0 记忆后端（实现底座 MemoryBackend ABC）。

M3 拼装核心：以 mem0ai 为底层引擎，对外暴露 OpenJarvis 底座
MemoryBackend 契约（store / retrieve / delete），供 Jarvis 记忆原语使用。

实现要点（对齐 tech-progression-plan §2）：
1. 接口对齐：MemoryBackend ABC（store→doc_id / retrieve→top_k / delete）
2. 注册接入：@MemoryRegistry.register("mem0") + 驻留标记（resident）
3. 数据分层：user / session / agent 三层，映射到底座 data-model
4. 本地方案：ollama nomic-embed-text 做 embedding；FAISS 本地向量库
   （不需要起任何外部服务，离线可跑）

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from openjarvis.tools.storage._stubs import MemoryBackend, RetrievalResult

from ..slot_adapter import main_settings
from .registry import MemoryRegistry

# mem0 后端默认向量库路径（相对 UltimaAgent 数据目录）
_DEFAULT_INDEX_DIR = os.path.join(
    os.environ.get("ULTIMA_AGENT_DATA", r"H:\UltimaAI\UltimaAgent\data"),
    "memory",
    "faiss",
)


class Mem0Backend(MemoryBackend):
    """基于 mem0ai 的记忆后端。

    Parameters
    ----------
    data_dir:
        FAISS 索引与元数据持久化目录。默认 data\\memory\\faiss。
    embedding_model:
        ollama 嵌入模型名（默认 nomic-embed-text，274MB 已拉取）。
    ollama_base_url:
        ollama 服务地址（默认取 S-MAIN 生效 endpoint）。
    memory_type:
        记忆粒度："user"（用户级）| "session"（会话级）| "agent"（Agent 级）。
    auto_registry:
        是否自动注册进 MemoryRegistry（驻留标记）。默认 True。
    """

    backend_id = "mem0"

    def __init__(
        self,
        data_dir: Optional[str] = None,
        *,
        embedding_model: str = "nomic-embed-text",
        memory_llm_model: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
        memory_type: str = "user",
        auto_registry: bool = True,
    ) -> None:
        if memory_type not in ("user", "session", "agent"):
            raise ValueError(f"memory_type 必须是 user/session/agent，got {memory_type!r}")
        self._memory_type = memory_type
        self._data_dir = data_dir or _DEFAULT_INDEX_DIR
        self._embedding_model = embedding_model
        effective_main = (
            main_settings()
            if memory_llm_model is None or ollama_base_url is None
            else None
        )
        self._memory_llm_model = (
            memory_llm_model
            if memory_llm_model is not None
            else str(effective_main["model"])
        )
        self._ollama_base_url = (
            ollama_base_url
            if ollama_base_url is not None
            else str(effective_main["endpoint"])
        )

        os.makedirs(self._data_dir, exist_ok=True)

        self._mem0 = self._build_mem0()

        if auto_registry and not MemoryRegistry.is_registered(self.backend_id):
            MemoryRegistry.register(
                self.backend_id,
                self,
                resident=True,
                description=f"Mem0 记忆后端（L9，{memory_type} 层，驻留）",
            )

    # ------------------------------------------------------------------
    # mem0 引擎构建
    # ------------------------------------------------------------------
    def _build_mem0(self):
        """构建 mem0 Memory 实例（ollama embed + FAISS 本地向量库）。"""
        from mem0 import Memory
        from mem0.configs.base import MemoryConfig
        from mem0.embeddings.configs import EmbedderConfig
        from mem0.llms.configs import LlmConfig
        from mem0.vector_stores.configs import VectorStoreConfig

        embedder_config = EmbedderConfig(
            provider="ollama",
            config={
                "model": self._embedding_model,
                "ollama_base_url": self._ollama_base_url,
                "embedding_dims": self._embedding_dims(),
            },
        )

        vector_store_config = VectorStoreConfig(
            provider="faiss",
            config={
                "path": self._data_dir,
                "embedding_model_dims": self._embedding_dims(),
            },
        )

        # 记忆提取复用 S-MAIN 的本地 LLM，无需外部 API key。
        llm_config = LlmConfig(
            provider="ollama",
            config={
                "model": self._memory_llm_model,
                "ollama_base_url": self._ollama_base_url,
                "temperature": 0.1,
                "max_tokens": 2000,
                "top_p": 0.1,
                "top_k": 1,
            },
        )

        memory_config = MemoryConfig(
            embedder=embedder_config,
            vector_store=vector_store_config,
            llm=llm_config,
        )
        # Memory.from_config 期望 dict（内部再构 MemoryConfig）
        return Memory.from_config(memory_config.model_dump())

    def _embedding_dims(self) -> int:
        """返回 embedding 向量维度（nomic-embed-text = 768）。"""
        # 提供可配置覆盖点；默认按 nomic-embed-text 实际维度
        return int(os.environ.get("ULTIMA_EMBED_DIMS", "768"))

    # ------------------------------------------------------------------
    # MemoryBackend ABC
    # ------------------------------------------------------------------
    def store(
        self,
        content: str,
        *,
        source: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """持久化 *content*，返回文档 ID。

        元数据映射：metadata.user_id / agent_id 决定层级归属；
        run_id（或 metadata.session_id）映射会话层。
        """
        meta = dict(metadata or {})
        user_id = meta.pop("user_id", "default")
        agent_id = meta.pop("agent_id", "ultima-agent")
        run_id = meta.pop("session_id", None) or meta.pop("run_id", None) or "default"

        result = self._mem0.add(
            content,
            user_id=user_id,
            agent_id=agent_id,
            run_id=run_id,
            metadata=meta,
            infer=False,
        )
        # mem0.add 返回 {"results": [{"id": ..., "event": ...}, ...]}
        items = result.get("results", []) if isinstance(result, dict) else result
        if items:
            return str(items[0].get("id", ""))
        return str(result)

    def retrieve(
        self,
        query: str,
        *,
        top_k: int = 5,
        **kwargs: Any,
    ) -> List[RetrievalResult]:
        """检索 *query*，返回 top_k 条记忆。

        未指定 user/agent 时按本后端 memory_type 对应默认值。
        """
        user_id = kwargs.get("user_id", "default")
        agent_id = kwargs.get("agent_id", "ultima-agent")
        run_id = kwargs.get("session_id") or kwargs.get("run_id")

        filters: Dict[str, Any] = {"user_id": user_id, "agent_id": agent_id}
        if run_id:
            filters["run_id"] = run_id

        results = self._mem0.search(
            query,
            limit=top_k,
            filters=filters,
        )
        # mem0.search 返回 {"results": [MemoryItem dict, ...]}
        items = results.get("results", []) if isinstance(results, dict) else results
        out: List[RetrievalResult] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            out.append(
                RetrievalResult(
                    content=str(item.get("memory", "")),
                    score=float(item.get("score", 0.0)),
                    source="mem0",
                    metadata=item,
                )
            )
        return out

    def delete(self, doc_id: str) -> bool:
        """删除指定记忆（mem0.delete 按记忆 id）。"""
        try:
            self._mem0.delete(memory_id=doc_id)
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """清空全部记忆（mem0.delete_all）。"""
        try:
            self._mem0.delete_all()
        except Exception:
            # mem0.delete_all 依赖 user_id 等参数；无参数版本兜底
            self._mem0.delete_all(user_id="default")

    # ------------------------------------------------------------------
    # 会话级扩展（供上层使用）
    # ------------------------------------------------------------------
    def add_session(
        self,
        content: str,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """显式写入会话层记忆（run_id 映射多轮对话上下文）。"""
        meta = dict(metadata or {})
        result = self._mem0.add(
            content,
            user_id=user_id,
            agent_id="ultima-agent",
            run_id=session_id,
            metadata=meta,
            infer=False,
        )
        items = result.get("results", []) if isinstance(result, dict) else result
        if items:
            return str(items[0].get("id", ""))
        return str(result)

    def snapshot(self) -> dict:
        """返回后端快照（供审计）。"""
        return {
            "backend_id": self.backend_id,
            "memory_type": self._memory_type,
            "embedding_model": self._embedding_model,
            "ollama_base_url": self._ollama_base_url,
            "data_dir": self._data_dir,
            "resident": MemoryRegistry.is_resident(self.backend_id),
        }


__all__ = ["Mem0Backend", "RetrievalResult"]
