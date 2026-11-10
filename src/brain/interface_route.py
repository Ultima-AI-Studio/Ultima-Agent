#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""配置表驱动的取数直达（对话主链用）。

一句话流程：
    用户问 → 配置里有这条意图且首选可用 → 直接取数作答（静默，几十毫秒）
    用户问 → 配置里没这条意图，或配了但一个可用首选都没有 → 现场从种子册建路
             （1 主 + 2 备，几秒内），建完立刻用它答，同时写回配置文件
    第二次再问 → 命中已写回的意图，直接作答，不重建

分工边界：
- 选哪家源、谁当主干：配置表 `config/interface-routing.json`
- 有哪些源可选：种子册 `config/interface-seeds.json`（含 catalog 意图元信息）
- 建路/巡检：tools/interface_build.py、tools/interface_probe.py
- 本模块只负责：识别意图 → 取数 → 把原始响应解析成模板字段 → 渲染成一句话

为什么不把解析规则写进配置：
各家的响应格式是供应商私有契约（新浪是逗号分列、itboy 是嵌套 JSON），
写成配置反而更难维护；这里按 endpoint 归口到固定解析器，新增供应商要加
解析器代码——这是诚实的边界，不假装"纯配置能接任何源"。
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "interface-routing.json"
SEEDS_PATH = ROOT / "config" / "interface-seeds.json"
TOOLS_DIR = ROOT / "tools"

# 对话里建路的时间上限：超过就先用手上已测通的，剩下的不拖住这轮回答。
AUTOBUILD_BUDGET_MS = 2500

_CACHE: dict = {"cfg": None, "cfg_mtime": None, "seeds": None, "seeds_mtime": None}

_ROLE_ORDER = {"primary": 0, "standby": 1, "fallback": 2}


# ── 配置 / 种子册加载（按 mtime 缓存，写回后自动失效）──────────────
def load_cfg(force: bool = False) -> dict:
    mt = CONFIG_PATH.stat().st_mtime
    if force or _CACHE["cfg"] is None or _CACHE["cfg_mtime"] != mt:
        _CACHE["cfg"] = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        _CACHE["cfg_mtime"] = mt
    return _CACHE["cfg"]


def load_seeds(force: bool = False) -> dict:
    mt = SEEDS_PATH.stat().st_mtime
    if force or _CACHE["seeds"] is None or _CACHE["seeds_mtime"] != mt:
        _CACHE["seeds"] = json.loads(SEEDS_PATH.read_text(encoding="utf-8"))
        _CACHE["seeds_mtime"] = mt
    return _CACHE["seeds"]


# ── 意图识别 ──────────────────────────────────────────────────────
def match_intent(text: str) -> tuple[str, dict | None, dict | None]:
    """返回 (kind, intent, catalog_entry)。

    kind = "intent"  配置里已有这条意图（可能缺首选，需要建路）
    kind = "new"     种子册认识这个标的，但配置里还没这条意图（要新建）
    kind = ("miss", None, None)
    """
    cfg = load_cfg()

    best_len, best = 0, None
    for it in cfg.get("intents", []):
        if it.get("route") != "http_direct":
            continue
        for trig in it.get("triggers") or []:
            if trig and trig in text and len(trig) > best_len:
                best_len, best = len(trig), it
    if best is not None:
        return "intent", best, None

    seeds = load_seeds()
    catalog = seeds.get("catalog") or {}
    known_assets = {it.get("asset") for it in cfg.get("intents", [])}

    best_len, best_asset = 0, None
    for asset, meta in catalog.items():
        if asset in known_assets:
            continue  # 配置里已有，走上面的意图匹配
        for trig in meta.get("triggers") or []:
            if trig and trig in text and len(trig) > best_len:
                best_len, best_asset = len(trig), asset
    if best_asset:
        entry = dict(catalog[best_asset])
        entry["asset"] = best_asset
        return "new", None, entry
    return "miss", None, None


# ── 取数 ──────────────────────────────────────────────────────────
def _http_get(url: str, headers: dict, timeout_ms: int) -> str | None:
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=max(timeout_ms, 200) / 1000) as resp:
            if resp.status != 200:
                return None
            body = resp.read()
    except Exception:
        return None
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        return body.decode("gbk", errors="replace")


def _num(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f


def _pct(cur, prev) -> str | None:
    c, p = _num(cur), _num(prev)
    if c is None or not p:
        return None
    return f"{(c - p) / p * 100:+.2f}%"


def _fmt(v, ndigits: int = 2) -> str | None:
    f = _num(v)
    return None if f is None else f"{f:.{ndigits}f}"


# ── 各供应商解析器：把原始响应转成模板字段 ─────────────────────────
def _parse_sina(text: str, asset: str) -> dict | None:
    m = re.search(r'="([^"]*)"', text)
    if not m:
        return None
    f = m.group(1).split(",")
    if len(f) < 5:
        return None

    if asset in ("index.cn", "stock.cn"):
        if len(f) < 10:
            return None
        price = _num(f[3]) or _num(f[1])
        return {
            "name": f[0],
            "price": _fmt(price),
            "change_pct": _pct(price, f[2]),
            "volume": _fmt(_num(f[8]) / 1e8 if _num(f[8]) is not None else None),
        }

    if asset in ("gold.intl", "gold.comex", "gold.cn", "silver.intl", "oil.wti", "oil.brent"):
        if len(f) < 9:
            return None
        price = _num(f[0])
        prev = _num(f[7])
        name = f[13] if len(f) > 13 and f[13] else ""
        return {
            "name": name,
            "price": _fmt(price),
            "change_pct": _pct(price, prev),
            "unit": "",
        }

    if asset == "index.hk":
        if len(f) < 12:
            return None
        # 港股字段：[2]今开 [3]昨收 [6]现价 —— 现价必须取 [6]，取 [2] 会答成开盘价
        return {
            "name": f[1],
            "price": _fmt(f[6]),
            "change_pct": f"{_num(f[8]):+.2f}%" if _num(f[8]) is not None else None,
            "volume": _fmt(_num(f[11]) / 1e8 if _num(f[11]) is not None else None),
        }

    if asset.startswith("index.us"):
        return {
            "name": f[0],
            "price": _fmt(f[1]),
            "change_pct": f"{_num(f[2]):+.2f}%" if _num(f[2]) is not None else None,
        }

    if asset == "fx.usdcny":
        rate = _num(f[8]) or _num(f[1])
        return {"rate": _fmt(rate, 4), "price": _fmt(rate, 4)}

    return None


def _parse_itboy(text: str, asset: str = "") -> dict | None:
    try:
        j = json.loads(text)
    except Exception:
        return None
    data = j.get("data") or {}
    forecasts = data.get("forecast") or []
    if not forecasts:
        return None
    day = forecasts[0]
    city = (j.get("cityInfo") or {}).get("city") or ""
    city = city.replace("市", "").replace("自治州", "").strip()

    def _t(field):
        m = re.search(r"-?\d+", str(day.get(field) or ""))
        return int(m.group()) if m else None

    return {
        "city": city,
        "condition": day.get("type") or "",
        "temp_low": _t("low"),
        "temp_high": _t("high"),
        "wind": f"{day.get('fx') or ''}{day.get('fl') or ''}" or None,
        "humidity": data.get("shidu"),
    }


_WTTR_ZH = {
    "sunny": "晴", "clear": "晴", "partly cloudy": "多云", "cloudy": "多云", "overcast": "阴",
    "mist": "薄雾", "fog": "雾", "patchy rain possible": "可能有雨", "light rain": "小雨",
    "moderate rain": "中雨", "heavy rain": "大雨", "light drizzle": "毛毛雨",
    "light freezing rain": "小冻雨", "light snow": "小雪", "moderate snow": "中雪",
    "heavy snow": "大雪", "patchy snow possible": "可能有雪", "thundery outbreaks possible": "可能有雷雨",
}


def _parse_wttr(text: str, asset: str = "") -> dict | None:
    try:
        j = json.loads(text)
    except Exception:
        return None
    cur = (j.get("current_condition") or [{}])[0]
    day = (j.get("weather") or [{}])[0]
    desc = ((cur.get("weatherDesc") or [{}])[0].get("value") or "").strip()
    zh = _WTTR_ZH.get(desc.lower())
    if not zh:
        zh = ((cur.get("lang_zh") or [{}])[0].get("value") or "").strip() or desc
    return {
        "city": "",
        "condition": zh,
        "temp_low": _num(day.get("mintempC")),
        "temp_high": _num(day.get("maxtempC")),
        "wind": f"{cur.get('winddir16Point') or ''}{cur.get('windspeedKmph') or ''}公里每小时",
    }


def _parse_dingzhi(text: str, asset: str = "") -> dict | None:
    m = re.search(r"=\s*({.*})\s*;?\s*$", text.strip(), re.S)
    if not m:
        return None
    try:
        j = json.loads(m.group(1))
    except Exception:
        return None
    # 实际结构是 {"weatherinfo": {...}}，不是平铺字段
    info = j.get("weatherinfo") or j
    return {
        "city": "",
        "condition": info.get("weather") or "",
        "temp_low": None,
        "temp_high": None,
        "wind": None,
    }


_WEATHER_CODE_ZH = {
    0: "晴", 1: "多云", 2: "多云", 3: "阴", 45: "雾", 48: "雾",
    51: "小雨", 53: "小雨", 55: "小雨", 61: "雨", 63: "雨", 65: "大雨",
    71: "小雪", 73: "小雪", 75: "大雪", 80: "阵雨", 81: "阵雨", 82: "强阵雨",
    95: "雷阵雨", 96: "雷阵雨", 99: "雷阵雨",
}


def _parse_openmeteo(text: str, asset: str = "") -> dict | None:
    try:
        j = json.loads(text)
    except Exception:
        return None
    daily = j.get("daily") or {}
    tmax = (daily.get("temperature_2m_max") or [None])[0]
    tmin = (daily.get("temperature_2m_min") or [None])[0]
    code = (daily.get("weather_code") or [None])[0]
    return {
        "city": "",
        "condition": _WEATHER_CODE_ZH.get(code, "未知"),
        "temp_low": tmin,
        "temp_high": tmax,
        "wind": None,
    }


def _parser_for(endpoint: str):
    if "hq.sinajs.cn" in endpoint:
        return _parse_sina
    if "t.weather.itboy.net" in endpoint:
        return _parse_itboy
    if "wttr.in" in endpoint:
        return _parse_wttr
    if "d1.weather.com.cn/dingzhi" in endpoint:
        return _parse_dingzhi
    if "api.open-meteo.com" in endpoint:
        return _parse_openmeteo
    return None


# ── 渲染 ──────────────────────────────────────────────────────────
def render(template: str, values: dict) -> str | None:
    """模板占位符必须全有值，缺一个就判失败——宁可换下一条源，不答缺项的话。"""
    if not template:
        return None
    try:
        out = template.format(**values)
    except (KeyError, IndexError, ValueError):
        return None
    if "{" in out or "}" in out:
        return None
    return out.strip()


# ── 城市参数（天气类）──────────────────────────────────────────────
def _weather_params(text: str, defaults: dict) -> dict:
    try:
        from .weather import _CITY_CODES, _extract_city  # 复用既有约 60 城对照表
    except Exception:
        return {}
    city = _extract_city(text)
    if not city:
        return {}
    code = _CITY_CODES.get(city)
    if not code:
        return {}
    return {"city_code": code, "city_name": city}


def _fill_params(text: str, defaults: dict) -> dict:
    merged = dict(defaults)
    weather = _weather_params(text, defaults) or {}
    merged.update(weather)
    # wttr.in 的 {city} 走城市名；缺这个位置参数会把请求打到默认位置，
    # 答出来的不是用户所在城市——宁可先填上，不能让备用源答错地方。
    if weather.get("city_name"):
        merged["city"] = weather["city_name"]
    return merged


# ── 主流程 ────────────────────────────────────────────────────────
def _ordered_candidates(intent: dict) -> list:
    return sorted(
        intent.get("candidates") or [],
        key=lambda c: _ROLE_ORDER.get(c.get("role"), 9),
    )


def _fetch_answer(intent: dict, text: str) -> tuple[str, dict] | None:
    cfg = load_cfg()
    params = _fill_params(text, cfg.get("defaults") or {})
    timeout_ms = int(intent.get("timeout_ms") or 5000)

    for cand in _ordered_candidates(intent):
        parser = _parser_for(cand.get("endpoint") or "")
        if parser is None:
            continue
        url = (cand.get("endpoint") or "")
        for key in ("{city_code}", "{city}", "{lat}", "{lon}", "{code}"):
            if key in url:
                url = url.replace(key, str(params.get(key.strip("{}"), "")))
        if "{" in url:
            continue  # 运行时实参（个股代码等）本轮不猜

        t0 = time.perf_counter()
        raw = _http_get(url, cand.get("headers") or {}, timeout_ms)
        ms = int((time.perf_counter() - t0) * 1000)
        if not raw:
            continue

        values = parser(raw, intent.get("asset") or "")
        if not values:
            continue
        values.setdefault("city", params.get("city_name") or "")
        if not values.get("city"):
            values["city"] = params.get("city_name") or ""

        answer = render(intent.get("template") or "", values)
        if not answer:
            continue
        return answer, {
            "intent": intent.get("id"),
            "endpoint": cand.get("endpoint"),
            "role": cand.get("role"),
            "coverage": cand.get("coverage"),
            "latency_ms": ms,
        }
    return None


def _build_and_reload(intent_id: str, meta: dict) -> dict | None:
    """现场建路并写回；返回刷新后的意图。"""
    import sys

    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from interface_build import build_intent  # 延迟导入，避免启动期副作用

    payload = build_intent(
        intent_id,
        asset=meta.get("asset") or "",
        requires=list(meta.get("requires") or []),
        label=meta.get("label") or "",
        triggers=list(meta.get("triggers") or []),
        template=meta.get("template") or "",
        budget_ms=AUTOBUILD_BUDGET_MS,
    )
    if payload.get("code") not in (0, None):
        return None

    cfg = load_cfg(force=True)
    return next((i for i in cfg.get("intents", []) if i.get("id") == intent_id), None)


def answer(text: str) -> tuple[str, dict] | None:
    """主入口：命中就返回 (一句话答案, 元信息)；没命中/取不到数返回 None。

    元信息里 built=True 表示这一轮是现场建的路（上层可用它决定要不要提一句）。
    """
    kind, intent, meta = match_intent(text)
    if kind == "miss":
        return None

    built = False
    if kind == "new":
        meta = dict(meta or {})
        meta["asset"] = meta.get("asset") or ""
        intent = next(
            (i for i in load_cfg().get("intents", []) if i.get("asset") == meta["asset"]),
            None,
        )
        if intent is None:
            intent_id = meta.get("intent_id") or f"market.{meta['asset'].replace('.', '_')}"
            intent = _build_and_reload(intent_id, meta)
            built = True
    elif not any(c.get("role") == "primary" for c in intent.get("candidates") or []):
        intent = _build_and_reload(
            intent.get("id"),
            {
                "asset": intent.get("asset"),
                "requires": intent.get("requires_coverage") or [],
                "label": intent.get("label") or "",
                "triggers": intent.get("triggers") or [],
                "template": intent.get("template") or "",
            },
        )
        built = True

    if intent is None:
        return None

    result = _fetch_answer(intent, text)
    if result is None:
        return None

    reply, info = result
    info["built"] = built
    info["degraded"] = bool((intent.get("build_state") or {}).get("degraded"))
    return reply, info


__all__ = ["answer", "match_intent", "load_cfg", "load_seeds", "AUTOBUILD_BUDGET_MS"]
