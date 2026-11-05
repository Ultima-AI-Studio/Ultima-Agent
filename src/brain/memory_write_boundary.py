"""Product memory-write seam protected by the P0 PoisonGuard."""

from __future__ import annotations

from typing import Any

from src.memory.writer import GuardedMemoryWriter


def guarded_memory_write(
    memory: Any,
    layer: str,
    content: str,
    **write_options: Any,
) -> Any:
    """Validate content before invoking the existing MemoryLayers.write API."""

    writer = GuardedMemoryWriter(
        lambda safe_content: memory.write(layer, safe_content, **write_options)
    )
    return writer.write(content)


__all__ = ["guarded_memory_write"]
