"""L3 环境认知：启动即环境快照（P1 补建）。

按 product-plan v2.3 L3 口径：启动即环境快照——硬件 / 磁盘 / 文件 / 应用扫描，
产出一份结构化快照供 L1 意图补全与 L3 执行接入消费。

设计约束：
- 不引入第三方依赖（仅标准库），保证在底座 venv 与任意 Python 3.10+ 可运行；
- 快照只读系统信息，不修改任何外部状态；
- 单次扫描控制在秒级（2 秒内），超时项降级为 null 并记录；
- 快照结构稳定（字段名固定），便于下游按契约消费。
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 快照版本：字段结构变更必须递增
SNAPSHOT_VERSION = "1.0.0"


def capture_work_context(*, provider):
    """Capture only the explicitly approved current object, on demand."""
    return provider.capture_work_context()


def validate_work_target(context: dict, *, provider) -> bool:
    return provider.validate_work_target(context)

_TIMEOUT_SECONDS = 2.0


@dataclass
class DiskInfo:
    mount: str
    total_gb: float
    free_gb: float
    used_gb: float
    filesystem: str = ""


@dataclass
class HardwareInfo:
    cpu_model: str = ""
    cpu_cores: int = 0
    cpu_logical: int = 0
    memory_total_gb: float = 0.0
    memory_available_gb: float = 0.0
    gpu: list[str] = field(default_factory=list)
    os_name: str = ""
    os_version: str = ""
    arch: str = ""


@dataclass
class FileInfo:
    path: str
    exists: bool
    is_dir: bool = False
    size_mb: float | None = None
    readable: bool = False
    note: str = ""


@dataclass
class AppInfo:
    name: str
    executable: str = ""
    window_title: str = ""


@dataclass
class EnvironmentSnapshot:
    version: str = SNAPSHOT_VERSION
    captured_at: str = ""
    hostname: str = ""
    user: str = ""
    hardware: HardwareInfo = field(default_factory=HardwareInfo)
    disks: list[DiskInfo] = field(default_factory=list)
    files: list[FileInfo] = field(default_factory=list)
    apps: list[AppInfo] = field(default_factory=list)
    env_keys: list[str] = field(default_factory=list)
    timed_out: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def _run_cmd(args: list[str], timeout: float = _TIMEOUT_SECONDS) -> str:
    """只读命令快照；超时或失败返回空串并登记 timed_out。

    Windows 下 PowerShell 子进程输出按系统代码页（如 GBK）编码，
    用二进制读取 + 宽松解码（errors="replace"），避免 UnicodeDecodeError。
    """
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = proc.stdout
        if out is None:
            return ""
        # 先按 UTF-8 试解（PowerShell 5.1+ 多输出 UTF-8），失败回退 GBK/宽松
        try:
            return out.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                return out.decode("gbk").strip()
            except UnicodeDecodeError:
                return out.decode("utf-8", errors="replace").strip()
    except Exception:  # noqa: BLE001 超时/不存在/非零均降级
        return ""


def scan_hardware() -> tuple[HardwareInfo, list[str]]:
    hw = HardwareInfo(
        os_name=platform.system(),
        os_version=platform.version(),
        arch=platform.machine(),
    )
    timed: list[str] = []
    try:
        import psutil  # 可选加速；底座 venv 未装则走标准库
    except ImportError:
        psutil = None  # type: ignore[assignment]

    if psutil is not None:
        try:
            hw.cpu_cores = psutil.cpu_count(logical=False) or 0
            hw.cpu_logical = psutil.cpu_count(logical=True) or 0
            mem = psutil.virtual_memory()
            hw.memory_total_gb = round(mem.total / (1024**3), 2)
            hw.memory_available_gb = round(mem.available / (1024**3), 2)
        except Exception:  # noqa: BLE001
            timed.append("hardware.psutil")
    else:
        try:
            hw.cpu_cores = os.cpu_count() or 0
            hw.cpu_logical = os.cpu_count() or 0
        except Exception:  # noqa: BLE001
            timed.append("hardware.cpu_count")

    # 内存：psutil 缺失时用标准库兜底（Windows: GlobalMemoryStatusEx；Linux: sysconf）
    if hw.memory_total_gb <= 0.0:
        try:
            if platform.system() == "Windows":
                import ctypes

                class _MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]

                state = _MEMORYSTATUSEX()
                state.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(state)):
                    hw.memory_total_gb = round(state.ullTotalPhys / (1024**3), 2)
                    hw.memory_available_gb = round(state.ullAvailPhys / (1024**3), 2)
                else:
                    timed.append("hardware.memory.ctypes")
            else:
                total_kb = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024
                hw.memory_total_gb = round(total_kb / (1024**2), 2)
                avail_kb = os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE") / 1024
                hw.memory_available_gb = round(avail_kb / (1024**2), 2)
        except Exception:  # noqa: BLE001
            timed.append("hardware.memory")

    # GPU（Windows：wmic 或 PowerShell CIM，均只读）
    gpu_raw = _run_cmd(["powershell", "-NoProfile", "-Command",
                        "(Get-CimInstance Win32_VideoController).Name"])
    hw.gpu = [g for g in gpu_raw.splitlines() if g.strip()]
    if not hw.gpu:
        gpu_raw2 = _run_cmd(["wmic", "path", "win32_videocontroller", "get", "name"])
        hw.gpu = [g.strip() for g in gpu_raw2.splitlines() if g.strip() and g.strip().lower() != "name"]

    cpu_raw = _run_cmd(["powershell", "-NoProfile", "-Command",
                        "(Get-CimInstance Win32_Processor).Name"])
    hw.cpu_model = (cpu_raw.splitlines() or [""])[0].strip()
    return hw, timed


def scan_disks() -> tuple[list[DiskInfo], list[str]]:
    disks: list[DiskInfo] = []
    timed: list[str] = []
    try:
        for part in os.scandir("\\"):
            pass  # Windows 根目录枚举
    except Exception:  # noqa: BLE001
        timed.append("disks.scandir")

    # 使用 shutil.disk_usage 遍历当前可用盘符。
    # 每盘在独立 daemon 线程中执行并限时（默认 5s/盘）：某些盘（大容量/
    # 网络映射/异常盘）的 disk_usage 或 exists 可能无限阻塞，直接把整个
    # 工具卡死到 ToolExecutor 的 future.result(timeout) 超时。
    import threading

    def _probe_disk(root: str, result: list, index: int) -> None:
        try:
            total, used, free = shutil.disk_usage(root)
            result[index] = (root, total, used, free)
        except Exception:  # noqa: BLE001
            result[index] = None

    for letter in "CDEFGH":
        root = f"{letter}:\\"
        try:
            if not os.path.exists(root):
                continue
        except Exception:  # noqa: BLE001  exists 本身也可能阻塞/抛错
            timed.append(f"disks.{letter}.exists")
            continue
        slot: list = [None]
        worker = threading.Thread(
            target=_probe_disk, args=(root, slot, 0), daemon=True
        )
        worker.start()
        worker.join(timeout=5.0)
        if worker.is_alive():
            timed.append(f"disks.{letter}.timeout")
            continue
        data = slot[0]
        if data is None:
            timed.append(f"disks.{letter}")
            continue
        _, total, used, free = data
        disks.append(
            DiskInfo(
                mount=root,
                total_gb=round(total / (1024**3), 2),
                free_gb=round(free / (1024**3), 2),
                used_gb=round(used / (1024**3), 2),
            )
        )
    return disks, timed


def scan_files(targets: list[str]) -> tuple[list[FileInfo], list[str]]:
    """指定关键目录/文件的存在性与大小（不递归全盘，避免超时）。"""
    files: list[FileInfo] = []
    timed: list[str] = []
    for raw in targets:
        p = Path(raw)
        try:
            exists = p.exists()
            info = FileInfo(path=str(p), exists=exists)
            if exists and p.is_dir():
                info.is_dir = True
                info.readable = os.access(p, os.R_OK)
            elif exists and p.is_file():
                try:
                    info.size_mb = round(p.stat().st_size / (1024**2), 2)
                    info.readable = os.access(p, os.R_OK)
                except Exception:  # noqa: BLE001
                    info.note = "stat 失败"
            files.append(info)
        except Exception:  # noqa: BLE001
            timed.append(f"files.{raw}")
    return files, timed


def scan_apps() -> tuple[list[AppInfo], list[str]]:
    """运行中的应用清单（进程名 + 窗口标题，只读）。"""
    apps: list[AppInfo] = []
    timed: list[str] = []
    raw = _run_cmd(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} "
         "| Select-Object ProcessName,MainWindowTitle,Path "
         "| ConvertTo-Json -Compress"],
        timeout=_TIMEOUT_SECONDS,
    )
    if raw:
        try:
            import json as _json

            items = _json.loads(raw)
            for it in items if isinstance(items, list) else [items]:
                apps.append(
                    AppInfo(
                        name=it.get("ProcessName", ""),
                        executable=it.get("Path") or "",
                        window_title=it.get("MainWindowTitle", ""),
                    )
                )
        except Exception:  # noqa: BLE001
            timed.append("apps.parse")
    return apps, timed


def capture_snapshot(
    file_targets: list[str] | None = None,
    include_env_keys: bool = True,
) -> EnvironmentSnapshot:
    """执行一次完整环境快照。file_targets 缺省用内置关键路径。"""
    if file_targets is None:
        file_targets = [
            r"H:\UltimaAI\UltimaAgent\tasks",
            r"H:\UltimaAI\UltimaAgent\src\brain\bootstrap.py",
            r"H:\UltimaAI\UltimaAgent\data",
            r"C:\Users\Administrator\.openjarvis\config.toml",
        ]

    snap = EnvironmentSnapshot(
        captured_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        hostname=platform.node(),
        user=os.environ.get("USERNAME") or os.environ.get("USER", ""),
    )
    snap.hardware, t1 = scan_hardware()
    snap.disks, t2 = scan_disks()
    snap.files, t3 = scan_files(file_targets)
    snap.apps, t4 = scan_apps()
    snap.timed_out = t1 + t2 + t3 + t4
    if include_env_keys:
        snap.env_keys = [k for k in sorted(os.environ.keys()) if not k.startswith("(")]
    return snap


def snapshot_to_file(snap: EnvironmentSnapshot, path: str) -> str:
    """将快照落盘到指定 JSON 文件；返回写入路径。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(snap.to_json(), encoding="utf-8")
    return str(target)


def load_snapshot(path: str) -> EnvironmentSnapshot | None:
    """从 JSON 恢复快照；缺失/损坏返回 None。"""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return EnvironmentSnapshot(**data)
    except Exception:  # noqa: BLE001
        return None


# 便捷入口：python src/brain/environment.py [输出路径]
if __name__ == "__main__":
    import sys

    out = sys.argv[1] if len(sys.argv) > 1 else str(
        Path(__file__).resolve().parents[2] / "data" / "environment" / "snapshot.json"
    )
    snapshot = capture_snapshot()
    written = snapshot_to_file(snapshot, out)
    print(snapshot.to_json())
    print(f"[written] {written}")
