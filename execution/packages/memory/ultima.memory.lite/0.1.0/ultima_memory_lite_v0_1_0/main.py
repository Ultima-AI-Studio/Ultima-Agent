"""L9 memory bus plugin — full four-layer memory base (s3-memory-base).

Keeps the frozen bus contract (memory.read / memory.write signatures),
internally wired to:
- MemoryLayers (working/declarative/procedural + device/env profiles)
- MemoryWriteGate (untrusted content blocked from long-term layers,
  fact/suggestion separated)
- ReflectionWriter (reflection entries into procedural)
- VectorRetriever (onnx embed primary, keyword fallback)

Call shapes:
- memory_read(query): str (keyword) | dict {query, layer, top_k}
- memory_write(fact): str (trusted=user) | dict {content, layer, kind, source, trusted}
"""

from __future__ import annotations

from pathlib import Path

from src.brain.memory import (
    MemoryLayers,
    MemoryWriteGate,
    ReflectionWriter,
    VectorRetriever,
)


class MemoryBasePlugin:
    def __init__(self, data_dir: str | Path | None = None) -> None:
        self._data_dir = Path(data_dir) if data_dir else Path(
            __file__).resolve().parents[6] / "data" / "memory"
        self._layers = MemoryLayers(self._data_dir)
        self._gate = MemoryWriteGate()
        self._reflections = ReflectionWriter(self._layers)
        self._vectors = VectorRetriever(self._layers, self._data_dir)

    def load(self) -> None:
        pass

    def activate(self) -> None:
        pass

    def disable(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def smoke(self) -> bool:
        return isinstance(self._layers.stats(), dict)

    # -- bus contract --------------------------------------------------------

    def memory_read(self, query):
        if isinstance(query, dict):
            q = str(query.get("query", ""))
            layer = query.get("layer")
            top_k = int(query.get("top_k", 5))
        else:
            q, layer, top_k = str(query or ""), None, 5
        if query is not None and isinstance(query, dict) and query.get("vector"):
            scored = self._vectors.search(q, layer=layer, top_k=top_k)
            return [{"id": e.id, "content": e.content, "layer": e.layer,
                     "kind": e.kind, "trusted": e.trusted, "score": round(s, 4)}
                    for e, s in scored]
        entries = self._layers.read(q, layer=layer, top_k=top_k)
        return [{"id": e.id, "content": e.content, "layer": e.layer,
                 "kind": e.kind, "trusted": e.trusted} for e in entries]

    def memory_write(self, fact):
        if isinstance(fact, dict):
            content = str(fact.get("content", ""))
            layer = str(fact.get("layer", "declarative"))
            kind = fact.get("kind")
            source = str(fact.get("source", "user"))
            meta = fact.get("meta", {})
        else:
            content, layer, kind, source, meta = str(fact or ""), "declarative", None, "user", {}
        if not content.strip():
            return {"stored": False, "denied": True, "reason": "empty"}
        decision = self._gate.assess(content, source=source, requested_layer=layer, kind=kind)
        if not decision.allow:
            return {"stored": False, "denied": True, "reason": decision.reason,
                    "target_layer": decision.target_layer, "kind": decision.kind}
        entry = self._layers.write(
            decision.target_layer, content,
            kind=decision.kind, trusted=(source in (
                "user", "tool", "bus.internal", "system", "engine")),
            source=source, meta=meta,
        )
        return {"stored": True, "id": entry.id, "layer": entry.layer,
                "kind": entry.kind, "trusted": entry.trusted}

    # -- extended (not in frozen contract; used via local import) -----------

    def memory_delete(self, entry_id):
        return {"deleted": self._layers.delete(entry_id)}

    def memory_layers(self):
        return self._layers.stats()

    def memory_reflect(self, content, target, outcome, note=""):
        ref = self._reflections.write(content, target=target, outcome=outcome, note=note)
        return {"id": ref.id, "layer": "procedural", "kind": "reflection"}

    def memory_forget(self):
        return {"evicted": self._layers.forget_expired()}


def create_plugin() -> MemoryBasePlugin:
    return MemoryBasePlugin()
