#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接口路由公共底座。

判断"一个源能不能用"的标准只维护这一份，巡检（interface_probe）与建路
（interface_build）都调它，避免两边各有一套口径。

判定四关，缺一不可：
  1) HTTP 200
  2) 能解码（UTF-8 优先，GBK 回退）
  3) 格式对（json 能解析）+ 关键字段在（must_contain 命中）
  4) 负载不是空壳（min_payload_bytes；专治 200 但内容为空串的情况）
"""

import json
import shutil
import statistics
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "interface-routing.json"
SEEDS = ROOT / "config" / "interface-seeds.json"
BACKUP_DIR = ROOT / "config" / "_backup"
CST = timezone(timedelta(hours=8))


def now_iso() -> str:
    return datetime.now(CST).isoformat(timespec="seconds")


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict, path: Path = CONFIG) -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(CST).strftime("%Y%m%d-%H%M%S")
    backup = BACKUP_DIR / f"{path.stem}-{stamp}.json"
    if path.exists():
        shutil.copy2(path, backup)
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)
    return backup


def build_url(tpl: str, defaults: dict) -> str:
    return (
        tpl.replace("{city_code}", str(defaults.get("city_code", "")))
        .replace("{city}", urllib.parse.quote(str(defaults.get("city_name", ""))))
        .replace("{lat}", str(defaults.get("lat", "")))
        .replace("{lon}", str(defaults.get("lon", "")))
    )


def probe_once(url: str, headers: dict, expect: dict, timeout_ms: int):
    """返回 (ok, ms, reason)。"""
    req = urllib.request.Request(url, headers=headers or {})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_ms / 1000) as resp:
            status = resp.status
            body = resp.read()
    except Exception as exc:  # 网络/超时/4xx/5xx 统一记失败
        return False, None, f"http:{type(exc).__name__}"
    ms = int((time.perf_counter() - t0) * 1000)
    if status != 200:
        return False, ms, f"status:{status}"

    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = body.decode("gbk", errors="replace")

    exp = expect or {}
    min_bytes = exp.get("min_payload_bytes")
    if min_bytes and len(body) < int(min_bytes):
        return False, ms, f"payload_too_small:{len(body)}"

    if exp.get("kind") == "json":
        try:
            json.loads(text)
        except Exception:
            return False, ms, "not_json"

    for token in exp.get("must_contain") or []:
        if token not in text:
            return False, ms, f"missing:{token}"

    return True, ms, "ok"


def probe_candidate(cand: dict, defaults: dict, policy: dict) -> dict:
    samples = policy["probe"]["samples_per_run"]
    timeout_ms = policy["probe"]["timeout_ms"]
    url = build_url(cand["endpoint"], defaults)

    results = [
        probe_once(url, cand.get("headers"), cand.get("expect"), timeout_ms)
        for _ in range(samples)
    ]
    ok_count = sum(1 for r in results if r[0])
    latencies = [r[1] for r in results if r[0] and r[1] is not None]
    p50 = int(statistics.median(latencies)) if latencies else None
    reasons = sorted({r[2] for r in results if not r[0]})
    return {
        "ok_count": ok_count,
        "samples": samples,
        "p50": p50,
        "ok_rate": round(ok_count / samples, 2),
        "fail_reasons": reasons,
    }


def apply_health(cand: dict, result: dict, requires: set) -> dict:
    h = cand.setdefault("health", {})
    if result["p50"] is not None:
        h["p50_ms"] = result["p50"]
    h["ok_rate"] = result["ok_rate"]
    h["probes"] = int(h.get("probes", 0)) + result["samples"]
    h["fail_streak"] = 0 if result["ok_count"] == result["samples"] else int(h.get("fail_streak", 0)) + 1
    h["last_probe_at"] = now_iso()
    h["eligible"] = requires.issubset(set(cand.get("provides") or []))
    if result["fail_reasons"]:
        h["last_error"] = ",".join(result["fail_reasons"])
    else:
        h.pop("last_error", None)
    return h
