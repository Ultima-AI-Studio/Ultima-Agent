"""G-ORCH 冒烟用纯函数，无 IO、无依赖。"""


def normalize_smoke(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("value must be a string or None")
    return value.strip().lower()
