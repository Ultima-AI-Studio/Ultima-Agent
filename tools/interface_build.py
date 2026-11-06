#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""首次建路器：给一个还没配过的意图，从种子库自动组装「1 条主干 + 2 条备用」。

和巡检器的分工：
- 本脚本负责"从无到有"：意图不存在或候选为空时，从 config/interface-seeds.json
  取同标的的源，现场探测，选出能用的，按快慢排好角色，写进配置。
- interface_probe.py 负责"从有到优"：已建好的路线定期体检、故障降级、速度升权。

铁律（写在代码里，不靠自觉）：
1. 只从种子库取源，不凭名字猜接口——猜出来的接口没人验证过，接上去就是答错。
2. 只取同一个标的的源（asset 必须完全一致），不同标的绝不混进一条路。
3. 每条候选都要过巡检同一套四关校验 + 覆盖度门禁；覆盖不全的不许当主干。
4. 同标的凑不满 3 条时如实标 degraded，不拿别的品种凑数。
5. 已配置且已有首选的意图默认不动（要重建得显式 --force）。

用法：
  python interface_build.py --intent market.oil_wti --asset oil.wti \
      --requires price,change_pct --label "WTI原油" --triggers "油价,WTI,原油" \
      --template "WTI 原油 {price} 美元/桶（{change_pct}）"

  python interface_build.py --config <临时配置> --intent weather.today --force --dry-run
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
    SEEDS,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TARGET_PRIMARY = 1
TARGET_STANDBY = 2


def emit(args, payload: dict, code: int = 0) -> int:
    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[建路] {payload.get('intent')} {payload.get('action')}")
        for line in payload.get("lines", []):
            print("  " + line)
        if payload.get("reason"):
            print("  原因：" + payload["reason"])
    return code


def collect_candidates(vendors: list, asset: str) -> list:
    out = []
    for v in vendors:
        for a in v.get("assets", []):
            if a.get("asset") != asset:
                continue
            tpl = v["endpoint_template"]
            code = a.get("code")
            endpoint = tpl.replace("{code}", code) if code else tpl
            cand = {
                "endpoint": endpoint,
                "headers": dict(v.get("headers") or {}),
                "expect": dict(v.get("expect") or {}),
                "provides": list(a.get("provides") or []),
                "role": "fallback",
                "health": {},
                "source_vendor": v["id"],
            }
            if a.get("display_name"):
                cand["display_name"] = a["display_name"]
            if a.get("unit"):
                cand["unit"] = a["unit"]
            if a.get("runtime_args"):
                cand["runtime_args"] = list(a["runtime_args"])
            if v.get("scope"):
                cand["scope"] = v["scope"]
            out.append(cand)
    return out


def evaluate(cands: list, defaults: dict, policy: dict, requires: set):
    """返回 (full, partial, unverified)。

    full      实测通过且字段覆盖够，能填满模板
    partial   能连上、有数据，但字段不全，只能降级作答（缺什么要在回复里说）
    unverified 含运行时实参占位符，本轮没法验证，等第一次真实调用再判
    """
    full, partial, unverified = [], [], []
    for c in cands:
        url = build_url(c["endpoint"], defaults)
        if "{" in url:
            # 运行时才知道的实参（如个股代码），本轮只能按声明判覆盖度
            c["health"] = {
                "p50_ms": None,
                "ok_rate": None,
                "probes": 0,
                "eligible": requires.issubset(set(c["provides"])),
                "probe": "skipped_runtime_args",
                "last_probe_at": now_iso(),
            }
            if c["health"]["eligible"]:
                unverified.append(c)
            continue
        res = probe_candidate(c, defaults, policy)
        apply_health(c, res, requires)
        c["health"]["probe"] = "live"
        ok = c["health"]["ok_rate"] >= 0.9 and c["health"].get("p50_ms") is not None
        if ok and c["health"]["eligible"]:
            full.append(c)
        elif ok:
            partial.append(c)
        elif res["fail_reasons"]:
            c["health"]["last_error"] = ",".join(res["fail_reasons"])
    return full, partial, unverified


def coverage_ratio(cand: dict, requires: set) -> float:
    if not requires:
        return 0.0
    return len(set(cand.get("provides") or []) & requires) / len(requires)


def assign_roles(cands: list, full: list, partial: list, unverified: list, requires: set):
    """凑「1 主 + 2 备」。完整源优先，不够时用降级源补位，绝不用别的标的凑数。

    降级源排序不只看快慢：先看它还能覆盖多少必需字段，字段覆盖一样多才比延迟。
    否则会把"最快但答不了晴雨"的源选成备用。
    """
    full.sort(key=lambda c: c["health"]["p50_ms"])
    partial.sort(key=lambda c: (-coverage_ratio(c, requires), c["health"]["p50_ms"]))
    ordered = full + partial + unverified
    picks = ordered[: TARGET_PRIMARY + TARGET_STANDBY]

    for c in cands:
        if c in picks:
            c["role"] = "primary" if picks.index(c) == 0 else "standby"
            c["coverage"] = "full" if c in full else ("partial" if c in partial else "unverified")
            if c["coverage"] == "partial":
                c["coverage_ratio"] = round(coverage_ratio(c, requires), 2)
                c["missing_fields"] = sorted(requires - set(c.get("provides") or []))
        else:
            c["role"] = "fallback"
            c["coverage"] = "none"
    return picks, len(picks) < TARGET_PRIMARY + TARGET_STANDBY


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(CONFIG))
    ap.add_argument("--intent", required=True)
    ap.add_argument("--asset", default="")
    ap.add_argument("--requires", default="")
    ap.add_argument("--label", default="")
    ap.add_argument("--triggers", default="")
    ap.add_argument("--template", default="")
    ap.add_argument("--cache", type=int, default=15)
    ap.add_argument("--timeout", type=int, default=5000)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    cfg = load_json(cfg_path)
    seeds = load_json(SEEDS)
    defaults = cfg["defaults"]
    policy = cfg["policy"]

    intent = next((i for i in cfg.get("intents", []) if i.get("id") == args.intent), None)

    if intent and intent.get("candidates"):
        has_primary = any(c.get("role") == "primary" for c in intent["candidates"])
        if has_primary and not args.force:
            return emit(args, {
                "intent": args.intent,
                "action": "skip_existing",
                "reason": "已配置且已有首选，直接复用，不重建",
                "lines": [f"现有候选 {len(intent['candidates'])} 条"],
            })

    asset = args.asset or (intent or {}).get("asset", "")
    if not asset:
        return emit(args, {"intent": args.intent, "action": "error",
                           "reason": "缺少 asset：不知道这条路查的是什么标的"}, 2)

    requires = [x.strip() for x in args.requires.replace("，", ",").split(",") if x.strip()]
    if not requires:
        requires = list((intent or {}).get("requires_coverage") or [])
    if not requires:
        return emit(args, {"intent": args.intent, "action": "error",
                           "reason": "缺少 requires：不知道这条通道要答哪些字段"}, 2)

    cands = collect_candidates(seeds.get("vendors", []), asset)
    if not cands:
        return emit(args, {"intent": args.intent, "action": "error",
                           "reason": f"种子库里没有标的 {asset} 的可用源，建不出路", "asset": asset}, 3)

    full, partial, unverified = evaluate(cands, defaults, policy, set(requires))
    picks, degraded = assign_roles(cands, full, partial, unverified, set(requires))

    if not picks:
        return emit(args, {"intent": args.intent, "action": "error",
                           "reason": "种子库里的候选本轮全部不可用，不建空路", "asset": asset}, 3)

    if intent is None:
        triggers = [x.strip() for x in args.triggers.replace("，", ",").split(",") if x.strip()]
        if not (args.label and triggers and args.template):
            return emit(args, {"intent": args.intent, "action": "error",
                               "reason": "新建意图必须给 label / triggers / template，否则这条路人根本命中不了"}, 2)
        intent = {
            "id": args.intent,
            "label": args.label,
            "asset": asset,
            "triggers": triggers,
            "requires_coverage": requires,
            "route": "http_direct",
            "timeout_ms": args.timeout,
            "cache_ttl_s": args.cache,
            "template": args.template,
            "candidates": [],
        }
        cfg.setdefault("intents", []).append(intent)
    else:
        intent["asset"] = asset
        intent.setdefault("requires_coverage", requires)

    intent["candidates"] = cands
    intent["built_by"] = "interface_build"
    intent["build_state"] = {
        "built_at": now_iso(),
        "asset": asset,
        "full": len(full),
        "partial": len(partial),
        "unverified": len(unverified),
        "picked": len(picks),
        "degraded": degraded,
        "target": {"primary": TARGET_PRIMARY, "standby": TARGET_STANDBY},
        "note": "partial 源字段不全，只在主干与完整备用都不可用时降级使用，回复里必须标注缺项。",
    }

    cfg.setdefault("changelog", []).append({
        "at": now_iso(),
        "action": "build",
        "detail": {
            "intent": args.intent,
            "asset": asset,
            "degraded": degraded,
            "picked": [
                {"endpoint": c["endpoint"], "role": c["role"], "coverage": c.get("coverage"), "p50_ms": c["health"].get("p50_ms")}
                for c in picks
            ],
        },
    })
    cfg["changelog"] = cfg["changelog"][-int(policy.get("history_max", 50)):]
    cfg["updated_at"] = now_iso()

    backup = None
    if not args.dry_run:
        backup = save_config(cfg, cfg_path)

    lines = []
    for c in picks:
        p50 = f"{c['health']['p50_ms']}ms" if c["health"].get("p50_ms") is not None else "待运行时首调验证"
        tag = "" if c.get("coverage") == "full" else f"（{c.get('coverage')}：字段不全，降级用）"
        lines.append(f"{c['role']:<8} {c['endpoint']}  {p50}{tag}")
    for c in cands:
        if c["role"] == "fallback" and c["health"].get("last_error"):
            lines.append(f"淘汰     {c['endpoint']}  {c['health']['last_error']}")
    if degraded:
        lines.append(f"注意：同标的本轮只有 {len(picks)} 条可用，凑不满 1 主 + 2 备，已标 degraded")

    return emit(args, {
        "intent": args.intent,
        "action": "built" if not args.dry_run else "built_dry_run",
        "asset": asset,
        "requires": requires,
        "full": len(full),
        "partial": len(partial),
        "unverified": len(unverified),
        "degraded": degraded,
        "backup": str(backup) if backup else None,
        "lines": lines,
    })


if __name__ == "__main__":
    sys.exit(main())
