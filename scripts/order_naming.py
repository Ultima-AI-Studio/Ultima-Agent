"""工单命名与卡片解析的唯一权威；其他位置不得再写第二份命名正则。"""

from __future__ import annotations

from pathlib import Path
import re


ORDER_ID_PATTERN = re.compile(r"wo-[a-z0-9]+(?:-[a-z0-9]+)*\Z")


def is_valid_order(order: str) -> bool:
    """Return whether *order* satisfies the canonical work-order grammar."""

    return isinstance(order, str) and ORDER_ID_PATTERN.fullmatch(order) is not None


def resolve_card_path(order: str, queue_dir: Path) -> Path:
    """Resolve the one direct or slugged queue card for *order*.

    The only accepted filenames are ``<order>.md`` and
    ``<order>--<non-empty-slug>.md``. Missing and ambiguous matches are both
    errors so callers cannot silently choose a card.
    """

    if not is_valid_order(order):
        raise ValueError(f"工单号不符合命名契约：{order!r}")

    queue_dir = Path(queue_dir)
    direct_name = f"{order}.md"
    slug_prefix = f"{order}--"
    try:
        entries = queue_dir.iterdir()
    except FileNotFoundError:
        entries = ()
    matches = sorted(
        (
            path
            for path in entries
            if path.is_file()
            and (
                path.name == direct_name
                or (
                    path.name.startswith(slug_prefix)
                    and path.name.endswith(".md")
                    and len(path.name) > len(slug_prefix) + len(".md")
                )
            )
        ),
        key=lambda path: path.name,
    )
    if len(matches) != 1:
        names = [path.name for path in matches]
        raise ValueError(
            f"工单卡解析失败：{order} 在 {queue_dir} 实际命中 {len(matches)} 张：{names}"
        )
    return matches[0]
