#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""接口快路径巡检器。

读 config/interface-routing.json，对每个 http_direct 意图的全部候选做四关校验
（HTTP 200 / 可解码 / 格式与关键字段 / 负载非空壳），并要求 provides 覆盖该意图
的 requires_coverage；跑 N 次取中位延迟，按实测重排 primary / standby / fallback
并写回配置。

分工：
- 建路（从无到有）由 interface_build.py 负责，它从 config/interface-seeds.json 取候选
- 本脚本只做"已有路线"的体检与升降级，不新增、不删除候选
- 换首选要有速度门槛（默认快 20% 以上），避免每天来回抖
- 每次写回前备份到 config/_backup/

用法：
  python interface_probe.py            # 正常巡检并写回
  python interface_probe.py --dry-run  # 只探测不写回
  python interface_probe.py --json     # 输出机器可读摘要
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from interface_common import (  # noqa: E402
    apply_health,
    build_url,
    load_json,
    now_iso,
    probe_candidate,
    save_config,
    CONFIG,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def rerank(intent: dict, policy: dict):
    """在健康候选里按延迟排序；换首选需满足速度门槛，避免抖动。

    full    = 字段覆盖够的；partial = 能连上有数据但字段不全的。
    主干只从 full 里选；备选先补 full，不够再用 partial 顶上，最多两条。
    """
    candidates = intent["candidates"]
    old_primary = next((c for c in candidates if c.get("role") == "primary"), None)

    for c in candidates:
        c.setdefault("health", {})

    demote_after = int((policy.get("demotion") or {}).get("fail_streak", 3))
    min_ok_rate = float((policy.get("promotion") or {}).get("min_ok_rate", 0.9))

    def usable(c):
        """能不能用。偶发波动（本轮 3 次采样里有 1 次失败）不判死刑，
        连续失败到 demote_after 才算坏——否则每天巡检都会因为一次超时来回换角色。"""
        h = c["health"]
        if h.get("p50_ms") is None:
            return False
        if h.get("fail_streak", 0) >= demote_after:
            return False
        rate = h.get("ok_rate", 0)
        return rate >= min_ok_rate or rate >= 0.5

    full = [c for c in candidates if c["health"].get("eligible") and usable(c)]
    full.sort(key=lambda c: c["health"]["p50_ms"])

    partial = [c for c in candidates if not c["health"].get("eligible") and usable(c)]
    requires = set(intent.get("requires_coverage") or [])
    partial.sort(key=lambda c: (
        -(len(set(c.get("provides") or []) & requires) / len(requires) if requires else 0),
        c["health"]["p50_ms"],
    ))

    if not full:
        for c in candidates:
            c["role"] = "fallback"
        return old_primary, None, []

    new_primary = full[0]
    threshold = policy["promotion"]["min_speed_gain_pct"]

    if (
        old_primary is not None
        and old_primary in full
        and new_primary is not old_primary
        and old_primary["health"]["p50_ms"]
    ):
        gain = (old_primary["health"]["p50_ms"] - new_primary["health"]["p50_ms"]) / old_primary["health"]["p50_ms"] * 100
        if gain < threshold:
            new_primary = old_primary

    standby_full = [c for c in full if c is not new_primary][:2]
    standby_partial = partial[: max(0, 2 - len(standby_full))]

    changes = []
    for c in candidates:
        if c is new_primary:
            role = "primary"
        elif c in standby_full or c in standby_partial:
            role = "standby"
        else:
            role = "fallback"
        c["coverage"] = "full" if c in full else ("partial" if c in partial else "none")
        if c["coverage"] == "partial" and requires:
            c["coverage_ratio"] = round(len(set(c.get("provides") or []) & requires) / len(requires), 2)
            c["missing_fields"] = sorted(requires - set(c.get("provides") or []))
        if c.get("role") != role:
            changes.append({
                "intent": intent["id"],
                "endpoint": c["endpoint"],
                "from": c.get("role"),
                "to": role,
            })
        c["role"] = role

    return old_primary, new_primary, changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    cfg = load_json(CONFIG)
    defaults = cfg["defaults"]
    policy = cfg["policy"]
    summary = []
    all_changes = []

    for intent in cfg["intents"]:
        if intent.get("route") != "http_direct":
            continue
        requires = set(intent.get("requires_coverage") or [])
        rows = []
        probed = 0
        for cand in intent.get("candidates", []):
            url = build_url(cand["endpoint"], defaults)
            if "{" in url:
                # 需要运行时才知道的占位符（如个股代码），本轮无法固定探测
                rows.append({
                    "endpoint": cand["endpoint"],
                    "p50_ms": cand.get("health", {}).get("p50_ms"),
                    "ok_rate": cand.get("health", {}).get("ok_rate"),
                    "eligible": cand.get("health", {}).get("eligible"),
                    "skipped": "模板占位符未解析",
                })
                continue
            probed += 1
            result = probe_candidate(cand, defaults, policy)
            apply_health(cand, result, requires)
            rows.append({
                "endpoint": cand["endpoint"],
                "p50_ms": cand["health"].get("p50_ms"),
                "ok_rate": cand["health"]["ok_rate"],
                "eligible": cand["health"]["eligible"],
                "last_error": cand["health"].get("last_error"),
            })

        if probed == 0:
            summary.append({
                "intent": intent["id"],
                "primary": next((c["endpoint"] for c in intent.get("candidates", []) if c.get("role") == "primary"), None),
                "primary_p50_ms": None,
                "switched_from": None,
                "candidates": rows,
                "skipped_all": True,
            })
            continue

        old_primary, new_primary, changes = rerank(intent, policy)
        all_changes.extend(changes)
        summary.append({
            "intent": intent["id"],
            "primary": new_primary["endpoint"] if new_primary else None,
            "primary_p50_ms": new_primary["health"]["p50_ms"] if new_primary else None,
            "switched_from": old_primary["endpoint"] if (old_primary and new_primary and old_primary is not new_primary) else None,
            "candidates": rows,
        })

    cfg["updated_at"] = now_iso()
    if all_changes:
        cfg.setdefault("changelog", []).append({
            "at": now_iso(),
            "action": "rerank",
            "detail": all_changes,
        })
        cfg["changelog"] = cfg["changelog"][-policy["history_max"]:]

    backup = None
    if not args.dry_run:
        backup = save_config(cfg)

    if args.as_json:
        print(json.dumps({
            "updated_at": cfg["updated_at"],
            "dry_run": args.dry_run,
            "backup": str(backup) if backup else None,
            "switched": bool(all_changes),
            "intents": summary,
        }, ensure_ascii=False, indent=2))
        return 0

    print(f"[巡检] {cfg['updated_at']}  模式={'试跑' if args.dry_run else '写回'}")
    for item in summary:
        if item.get("skipped_all"):
            print(f"  {item['intent']:<18} 跳过（需运行时实参）")
            continue
        p50 = f"{item['primary_p50_ms']}ms" if item["primary_p50_ms"] is not None else "无可用"
        flag = f"  ← 切换自 {item['switched_from']}" if item["switched_from"] else ""
        print(f"  {item['intent']:<18} 首选 {p50:<8}{flag}")
    for item in summary:
        for c in item["candidates"]:
            if c.get("last_error"):
                print(f"    备选异常 {c['endpoint']} {c['last_error']}")

    # 只有"某意图找不到可用首选"才算巡检失败；备选掉线属正常波动
    measurements_ok = all(
        item.get("skipped_all") or item["primary_p50_ms"] is not None
        for item in summary
    )
    if backup:
        print(f"[备份] {backup}")
    return 0 if measurements_ok else 1


if __name__ == "__main__":
    sys.exit(main())
