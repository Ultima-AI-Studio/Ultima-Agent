"""Read-only heartbeat and exit-anomaly sentinel for one queue run."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Sequence

from tasks.queue_engine.dispatcher import DispatchLock, process_identity


LOG_STALE_AFTER_S = 90.0


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class Sentinel:
    """Observe one worker without changing its process or queue state."""

    def __init__(
        self,
        order: str,
        run_dir: str | Path,
        pid: int,
        expected_identity: str,
        interval: float = 30,
        missed: int = 3,
    ) -> None:
        if not order:
            raise ValueError("order is required")
        if pid <= 0:
            raise ValueError("pid must be positive")
        if not expected_identity:
            raise ValueError("expected_identity is required")
        if interval <= 0:
            raise ValueError("interval must be positive")
        if missed <= 0:
            raise ValueError("missed must be positive")

        self.order = order
        self.run_dir = Path(run_dir)
        self.pid = pid
        self.expected_identity = expected_identity
        self.interval = float(interval)
        self.missed = missed
        self._consecutive = 0
        self._anomaly_active = False

    def _latest_log_age_s(self) -> float | None:
        candidates: list[Path] = []
        for pattern in ("*.log", "*.out", "*.err"):
            candidates.extend(path for path in self.run_dir.rglob(pattern) if path.is_file())
        if not candidates:
            return None
        latest_mtime = max(path.stat().st_mtime for path in candidates)
        return round(max(0.0, time.time() - latest_mtime), 6)

    def _append_heartbeat(self, heartbeat: dict[str, Any]) -> None:
        self.run_dir.mkdir(parents=True, exist_ok=True)
        with (self.run_dir / "heartbeat.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(heartbeat, ensure_ascii=False, separators=(",", ":")) + "\n")
            stream.flush()

    def tick(self) -> dict[str, Any]:
        """Record one observation and emit anomaly/recovery events when thresholds cross."""

        self.run_dir.mkdir(parents=True, exist_ok=True)
        heartbeat = {
            "ts": _utc_now(),
            "pid_alive": process_identity(self.pid) == self.expected_identity,
            "final_message": (self.run_dir / "final-message.json").is_file(),
            "log_age_s": self._latest_log_age_s(),
        }
        self._append_heartbeat(heartbeat)

        log_is_stale = heartbeat["log_age_s"] is None or heartbeat["log_age_s"] > LOG_STALE_AFTER_S
        is_anomalous = (
            not heartbeat["pid_alive"]
            and not heartbeat["final_message"]
            and log_is_stale
        )

        if is_anomalous:
            self._consecutive += 1
            if self._consecutive >= self.missed and not self._anomaly_active:
                _write_json(
                    self.run_dir / "anomaly.json",
                    {
                        "order": self.order,
                        "ts": heartbeat["ts"],
                        "kind": "exit-anomaly",
                        "evidence": heartbeat,
                        "consecutive": self._consecutive,
                    },
                )
                self._anomaly_active = True
        else:
            previous_consecutive = self._consecutive
            self._consecutive = 0
            if self._anomaly_active:
                _write_json(
                    self.run_dir / "recovered.json",
                    {
                        "order": self.order,
                        "ts": heartbeat["ts"],
                        "kind": "recovered",
                        "evidence": heartbeat,
                        "previous_consecutive": previous_consecutive,
                    },
                )
                self._anomaly_active = False

        return heartbeat

    def run(self, *, max_ticks: int | None = None) -> int:
        """Hold the per-run singleton lock and tick until interrupted."""

        lock = DispatchLock(self.run_dir / ".sentinel.lock")
        if not lock.acquire():
            return 2
        try:
            ticks = 0
            while max_ticks is None or ticks < max_ticks:
                self.tick()
                ticks += 1
                if max_ticks is None or ticks < max_ticks:
                    time.sleep(self.interval)
        except KeyboardInterrupt:
            return 0
        finally:
            lock.release()
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("order")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("pid", type=int)
    parser.add_argument("expected_identity")
    parser.add_argument("--interval", type=float, default=30.0)
    parser.add_argument("--missed", type=int, default=3)
    args = parser.parse_args(argv)
    return Sentinel(
        args.order,
        args.run_dir,
        args.pid,
        args.expected_identity,
        interval=args.interval,
        missed=args.missed,
    ).run()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["LOG_STALE_AFTER_S", "Sentinel", "main"]
