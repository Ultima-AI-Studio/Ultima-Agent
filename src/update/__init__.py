"""s1-remote-update 客户端更新通道（T1 通道库 + T2 三触发）。

- channel.UpdateChannel：查版本/下载/验签/替换回滚
- triggers.UpdateTriggerEngine：启动自检/手动检查/静默强制 + 状态机
"""
from .channel import (
    UpdateChannel,
    UpdateChannelError,
    UpdateInfo,
    UpdateResult,
    VersionQueryError,
    DownloadError,
    HashMismatchError,
    SignatureError,
    ReplaceError,
)
from .triggers import (
    UpdateTriggerEngine,
    UpdateState,
    IDLE,
    CHECKING,
    DOWNLOADING,
    AVAILABLE,
    UPDATING,
    UPDATED,
    FAILED,
)

__all__ = [
    "UpdateChannel",
    "UpdateChannelError",
    "UpdateInfo",
    "UpdateResult",
    "VersionQueryError",
    "DownloadError",
    "HashMismatchError",
    "SignatureError",
    "ReplaceError",
    "UpdateTriggerEngine",
    "UpdateState",
    "IDLE",
    "CHECKING",
    "DOWNLOADING",
    "AVAILABLE",
    "UPDATING",
    "UPDATED",
    "FAILED",
]
