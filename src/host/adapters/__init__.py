"""宿主抽象层适配器（Windows 文件契约实现）。"""

from .file_host import (
    FileHostEvents,
    FileHostIO,
    FileHostRenderer,
    build_file_host,
)

__all__ = ["FileHostIO", "FileHostRenderer", "FileHostEvents", "build_file_host"]
