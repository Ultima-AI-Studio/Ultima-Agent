"""天气直达模块（2026-10-29 新增）：识别天气意图后一句话秒答，不经过 8B。
2026-10-30 22:5x 扩展：解析时间词（今天/明天/后天），按目标日期取预报；
   修复真机"明天的上海天气怎么样"答"上海现在霾"（原实现只取 current_condition）。

数据源：wttr.in 公开天气接口（无需 key）。
- 城市定位：优先解析文本中的城市名；未指定时默认沈阳（用户所在地，见 L7 真机反馈）。
- 时间定位：今天/现在 → current_condition；明天/后天/大后天 → weather[] 对应日期。
- 返回："沈阳今天多云，气温 12~20 度，东南风 3 级。" 格式的一句话。
- 失败返回 None，由 interaction 层降级走 8B 兜底，不阻断主链路。

仅标准库 urllib，可在任意 Python 3.10+（含 venv-asr / venv-openjarvis）运行。
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# ── 城市名 → 中国天气网城市编码（覆盖常见城市 + 东北重点）─────────
_CITY_CODES: dict[str, str] = {
    # 东北
    "沈阳": "101070101",
    "大连": "101070201",
    "鞍山": "101070301",
    "抚顺": "101070401",
    "本溪": "101070501",
    "丹东": "101070601",
    "锦州": "101070701",
    "营口": "101070801",
    "阜新": "101070901",
    "辽阳": "101071001",
    "盘锦": "101071101",
    "铁岭": "101071201",
    "朝阳": "101071301",
    "葫芦岛": "101071401",
    "长春": "101060101",
    "吉林": "101060201",
    "哈尔滨": "101050101",
    "大庆": "101050901",
    "齐齐哈尔": "101050201",
    # 华北
    "北京": "101010100",
    "天津": "101030100",
    "石家庄": "101090101",
    "唐山": "101090501",
    "太原": "101100101",
    "呼和浩特": "101080101",
    # 华东
    "上海": "101020100",
    "南京": "101190101",
    "苏州": "101190401",
    "无锡": "101190201",
    "徐州": "101190801",
    "杭州": "101210101",
    "宁波": "101210401",
    "温州": "101210701",
    "合肥": "101220101",
    "福州": "101230101",
    "厦门": "101230201",
    "南昌": "101240101",
    "济南": "101120101",
    "青岛": "101120201",
    "烟台": "101120501",
    "威海": "101121301",
    # 华中
    "郑州": "101180101",
    "武汉": "101200101",
    "长沙": "101250101",
    # 华南
    "广州": "101280101",
    "深圳": "101280601",
    "珠海": "101280701",
    "佛山": "101280800",
    "东莞": "101281601",
    "南宁": "101300101",
    "海口": "101310101",
    # 西南
    "重庆": "101040100",
    "成都": "101270101",
    "绵阳": "101270401",
    "昆明": "101290101",
    "贵阳": "101260101",
    "拉萨": "101140101",
    # 西北
    "西安": "101110101",
    "兰州": "101160101",
    "西宁": "101150101",
    "银川": "101170101",
    "乌鲁木齐": "101130101",
    "呼和浩特": "101080101",
}

# 默认城市（用户所在地，真机反馈"查天气"未带城市时直查本地）
_DEFAULT_CITY = "沈阳"
_DEFAULT_CODE = "101070101"

# 文本中出现的城市名（按长度降序，避免"大连"被"大"吞）
_CITY_NAMES = sorted(_CITY_CODES, key=len, reverse=True)

_TIMEOUT_SECONDS = 8

# wttr.in 公开天气接口（无需 key，返回 JSON；用中文城市名参数，curl 模式下
# city 需 URL 编码；%20 与中文均可。示例：https://wttr.in/沈阳?format=j1）
_WEATHER_URL = "https://wttr.in/{city}?format=j1&lang=zh"


def _extract_city(text: str) -> str | None:
    """从指令文本中提取城市名；无城市信息返回 None（调用方用默认城市）。"""
    for name in _CITY_NAMES:
        if name in text:
            return name
    return None


# ── 时间词 → 预报日期偏移（2026-10-30 新增，修复"问明天答现在"）─────────
_TIME_LABELS = {1: "明天", 2: "后天", 3: "大后天"}


def _extract_day_offset(text: str) -> int:
    """从指令文本中提取日期偏移：今天/现在=0，明天=1，后天=2，大后天=3。"""
    if re.search(r"大后天|三天后|三日后|三天以后", text):
        return 3
    if re.search(r"后天|明后天", text):
        return 2
    if re.search(r"明天|明儿|明早|明晚|明日|明个", text):
        return 1
    return 0  # 今天 / 无时间词 → 当前天气


def _time_label(offset: int, text: str) -> str:
    """生成回答中的时间前缀：明天/后天/大后天；今天或无词用"现在"。"""
    if offset:
        return _TIME_LABELS[offset]
    if re.search(r"今天|今日|今晚", text):
        return "今天"
    return "现在"


def _fetch_weather(code: str, day_offset: int = 0) -> dict | None:
    """请求 wttr.in 天气接口，返回解析后的天气 dict；失败返回 None。

    2026-10-29 21:1x 加固：wttr.in 境外服务瞬时抖动（真机 21:07 轮 8s 超时 → None
    → 降级 8B 干等 40s 静默，用户反馈"查天气没回复"）。加重试一次（共 2 次），
    超时缩至 6s，总耗时 ≤12s。
    2026-10-30 22:5x 扩展：day_offset>0 时从 weather[] 预报数组取目标日期
    （mintempC/maxtempC + 白天 9/12/15 时天气描述），不再只回当前快照。
    """
    city = next((name for name, c in _CITY_CODES.items() if c == code), _DEFAULT_CITY)
    url = _WEATHER_URL.format(city=urllib.parse.quote(city))
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (UltimaAgent/1.0)"},
    )
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            break  # 成功
        except Exception as exc:  # 网络/JSON 异常：重试一次
            last_err = exc
            if attempt == 0:
                continue
            return None
    else:
        return None

    # 目标日期（预报数组按城市当地时间，date.today() 同源 UTC+8）
    target = (date.today() + timedelta(days=day_offset)).isoformat()

    if day_offset == 0:
        try:
            current = (payload.get("current_condition") or [{}])[0]
            weather_code = current.get("weatherCode") or current.get("weatherDesc") or ""
            desc = _weather_code_to_zh(weather_code)
            temp_c = current.get("temp_C")
            feels = current.get("FeelsLikeC")
            humidity = current.get("humidity")
            wind_dir = current.get("winddir16Point")
            wind_km = current.get("windspeedKmph")
        except Exception:
            return None
        return {
            "city": city,
            "temp_c": temp_c,
            "feels": feels,
            "humidity": humidity,
            "weather": desc,
            "wind": _wind_zh(wind_dir, wind_km),
        }

    # 未来某天：weather[] 数组按 date 匹配目标日期
    for day in payload.get("weather") or []:
        if str(day.get("date", "")) != target:
            continue
        desc = ""
        for h in day.get("hourly") or []:
            if str(h.get("time", "")) in ("900", "1200", "1500"):  # 白天 9/12/15 时
                d = _weather_code_to_zh(h.get("weatherCode"))
                if d and d != "未知":
                    desc = d
                    break
        return {
            "city": city,
            "weather": desc,
            "min_temp": day.get("mintempC"),
            "max_temp": day.get("maxtempC"),
            "day_offset": day_offset,
        }
    return None  # 目标日期不在预报窗口（wttr.in 默认 3 天）


# 16 方位英文缩写 → 中文（wttr.in winddir16Point）
_WIND_ZH = {
    "N": "北风", "NNE": "北偏东风", "NE": "东北风", "ENE": "东偏北风",
    "E": "东风", "ESE": "东偏南风", "SE": "东南风", "SSE": "南偏东风",
    "S": "南风", "SSW": "南偏西风", "SW": "西南风", "WSW": "西偏南风",
    "W": "西风", "WNW": "西偏北风", "NW": "西北风", "NNW": "北偏西风",
}


def _wind_zh(dir16: str | None, km: str | None) -> str:
    """方向缩写转中文 + 风力，如 SSW+14 → 南偏西风14公里每小时。"""
    if not dir16 or not km:
        return ""
    name = _WIND_ZH.get(dir16.strip().upper(), f"{dir16}风")
    return f"{name}{km}公里每小时"


# wttr.in weatherCode → 中文天气现象（wttr.in 官方 code 表，覆盖常见项）
_WEATHER_CODE_ZH = {
    113: "晴",
    116: "晴间多云",
    119: "多云",
    122: "阴",
    143: "雾",
    149: "霾",
    176: "零星阵雨",
    179: "零星雨雪",
    182: "雨夹雪",
    185: "冻雨",
    200: "雷阵雨",
    227: "小雪",
    230: "暴雪",
    248: "雾",
    260: "冻雾",
    263: "零星小雨",
    266: "小雨",
    281: "冻雨",
    284: "冻雨",
    293: "零星小雨",
    296: "小雨",
    299: "小到中雨",
    302: "中雨",
    305: "中到大雨",
    308: "大雨",
    311: "冻雨",
    314: "冻雨",
    317: "雨夹雪",
    320: "雨夹雪",
    323: "零星小雪",
    326: "小雪",
    329: "小到中雪",
    332: "中雪",
    335: "中到大雪",
    338: "大雪",
    350: "冻雨",
    353: "零星小雨",
    356: "小到中雨",
    359: "大雨",
    362: "雨夹雪",
    365: "雨夹雪",
    368: "零星小雪",
    371: "小雪",
    374: "冻雨",
    377: "冻雨",
    386: "雷阵雨",
    389: "雷雨",
    392: "雷雪",
    395: "雷雪",
}


_EN_DESC_ZH = {
    "clear": "晴",
    "sunny": "晴",
    "partly cloudy": "多云",
    "cloudy": "多云",
    "overcast": "阴",
    "mist": "雾",
    "fog": "雾",
    "freezing fog": "冻雾",
    "patchy rain": "零星小雨",
    "light rain": "小雨",
    "moderate rain": "中雨",
    "heavy rain": "大雨",
    "light rain shower": "阵雨",
    "moderate or heavy rain shower": "阵雨",
    "thundery outbreaks": "雷阵雨",
    "patchy snow": "零星小雪",
    "light snow": "小雪",
    "moderate snow": "中雪",
    "heavy snow": "大雪",
    "light sleet": "雨夹雪",
    "blizzard": "暴雪",
    "freezing rain": "冻雨",
}


def _weather_code_to_zh(code: str | int | None) -> str:
    if code is None:
        return "未知"
    if isinstance(code, str):
        key_lower = code.strip().lower()
        if key_lower.isdigit():
            return _WEATHER_CODE_ZH.get(int(key_lower), "未知")
        return _EN_DESC_ZH.get(key_lower, code.strip() or "未知")
    return _WEATHER_CODE_ZH.get(int(code), "未知")


def _format_answer(city: str, w: dict, label: str = "现在") -> str:
    """把天气 dict 拼成一句话口语回答。label 为时间前缀（现在/今天/明天/后天）。"""
    if w.get("day_offset"):
        # 未来某天：天气描述 + 最低/最高温
        weather = w.get("weather") or ""
        lo, hi = w.get("min_temp"), w.get("max_temp")
        if not weather:
            parts = [f"{city}{label}天气未知"]
        else:
            parts = [f"{city}{label}{weather}"]
        if lo and hi:
            parts.append(f"气温{lo}~{hi}度")
        return "，".join(parts) + "。"
    # 当前天气：保持既有口径
    weather = w.get("weather") or ""
    temp_c = w.get("temp_c")
    feels = w.get("feels")
    wind = w.get("wind") or ""
    parts = []
    if weather:
        parts.append(f"{city}{label}{weather}")
    else:
        parts.append(f"{city}{label}天气未知")
    if temp_c:
        parts.append(f"气温{temp_c}度")
    if feels and str(feels) != str(temp_c):
        parts.append(f"体感{feels}度")
    if wind:
        parts.append(wind)
    return "，".join(parts) + "。"


def query_weather(text: str) -> str | None:
    """对外入口：给定一句口语指令（如"查一下沈阳天气"/"明天上海的天气"），返回一句话天气回答。

    城市未指定时默认沈阳。时间词（今天/明天/后天）解析后取对应预报；无时间词取当前。
    任何异常/缺数据返回 None（上层降级走 8B）。
    """
    city = _extract_city(text) or _DEFAULT_CITY
    code = _CITY_CODES.get(city)
    if not code:
        return None
    offset = _extract_day_offset(text)
    label = _time_label(offset, text)
    info = _fetch_weather(code, offset)
    if not info:
        return None
    answer = _format_answer(city, info, label)
    # 极简自检：回答必须含城市与天气现象，否则视为失败
    if not answer or city not in answer or "未知" in answer:
        return None
    return answer


__all__ = ["query_weather"]
