#!/usr/bin/env python3
"""Read-only structural audit for the Next settings baseline."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "docs/specs/next-感知交互参数基线-20261113.md"
OUTPUT = Path(__file__).with_name("structure.json")

CN_DIGITS = {
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def chinese_number(value: str) -> int:
    if value in CN_DIGITS:
        return CN_DIGITS[value]
    if value.startswith("十"):
        return 10 + CN_DIGITS.get(value[1:], 0)
    if value.endswith("十"):
        return CN_DIGITS[value[:-1]] * 10
    tens, ones = value.split("十", 1)
    return CN_DIGITS[tens] * 10 + CN_DIGITS[ones]


def classify_pending(
    lines: list[str], index: int, token: str, *, appendix_history: bool
) -> tuple[str, str]:
    line = lines[index].rstrip("\r\n")
    context = "\n".join(
        part.rstrip("\r\n")
        for part in lines[max(0, index - 2) : min(len(lines), index + 3)]
    )
    if appendix_history:
        return "已有解释", "命中位于附录 A 变更记录，属于带日期的历史记录"
    if token == "待填" and (
        (
            re.search(r"sha256", context, re.IGNORECASE)
            and re.search(r"实测|到机|落盘|填写|填入|计算", context)
        )
        or re.search(r"\|\s*`mainbrain\.[^`]+`\s*\|.*\|\s*待填", line)
    ):
        return "运行时算值", "上下文同时给出 sha256/n_ctx 与实测、到机、落盘或填写动作"
    if token == "暂定" and re.search(
        r"用途|用于|阈值|口径|状态|检测|活动|停滞|时长|裁决", context
    ):
        return "显式暂定", "正文标为暂定，邻近上下文给出用途、口径、状态或阈值锚点"
    if re.search(
        r"R-\d+|裁决|说明|原因|解释|明确|已定|建议值|不进入|暂不|待 Owner|Owner 待定|Owner.*决定",
        context,
        re.IGNORECASE,
    ):
        return "已有解释", "邻近上下文含 R 编号、裁决/说明或明确的 Owner 决策状态"
    return "无解释待定", "未命中三类允许解释的客观锚点"


def main() -> int:
    with SOURCE.open("r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    lines = text.splitlines(keepends=True)

    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    cr = text.count("\r") - crlf
    if crlf and not lf and not cr:
        eol = "CRLF"
    elif lf and not crlf and not cr:
        eol = "LF"
    elif not (crlf or lf or cr):
        eol = "NONE"
    else:
        eol = "MIXED"

    chapter_re = re.compile(r"^##(?!#)\s*([一二三四五六七八九十]{1,3})、\s*(.*)$")
    level2_re = re.compile(r"^##(?!#)\s*(.*?)\s*$")
    heading3_re = re.compile(r"^###(?!#)\s*(.*?)\s*$")
    section_re = re.compile(r"^(\d+)\.(\d+)(?!\.)\s*(.*)$")
    deep_number_re = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?\s*(.*)$")

    chapters: list[dict[str, object]] = []
    sections: list[dict[str, object]] = []
    deep_sections: list[dict[str, object]] = []
    appendices: list[dict[str, object]] = []
    all_level2: list[dict[str, object]] = []
    all_level3: list[dict[str, object]] = []
    current_chapter: int | None = None

    for line_no, raw in enumerate(lines, 1):
        line = raw.rstrip("\r\n")
        level2 = level2_re.match(line)
        if level2:
            title = level2.group(1)
            all_level2.append({"line": line_no, "text": title})
            chapter = chapter_re.match(line)
            if chapter:
                number = chinese_number(chapter.group(1))
                current_chapter = number
                chapters.append(
                    {
                        "number": number,
                        "numeral": chapter.group(1),
                        "title": chapter.group(2).strip(),
                        "line": line_no,
                    }
                )
            else:
                appendices.append({"title": title, "line": line_no})
                current_chapter = None
            continue

        heading3 = heading3_re.match(line)
        if heading3:
            title = heading3.group(1)
            all_level3.append({"line": line_no, "text": title})
            deep = deep_number_re.match(title)
            if deep:
                deep_sections.append(
                    {
                        "number": ".".join(part for part in deep.groups()[:4] if part),
                        "title": deep.group(5).strip(),
                        "line": line_no,
                        "containing_chapter": current_chapter,
                    }
                )
                continue
            section = section_re.match(title)
            if section:
                sections.append(
                    {
                        "chapter": int(section.group(1)),
                        "section": int(section.group(2)),
                        "title": section.group(3).strip(),
                        "line": line_no,
                        "containing_chapter": current_chapter,
                    }
                )

    chapter_numbers = [int(item["number"]) for item in chapters]
    expected_chapters = list(range(1, 25))
    chapter_sequence_pass = chapter_numbers == expected_chapters

    section_sequences: list[dict[str, object]] = []
    section_sequence_pass = True
    for chapter_number in chapter_numbers:
        actual = [
            int(item["section"])
            for item in sections
            if item["chapter"] == chapter_number
        ]
        expected = list(range(1, len(actual) + 1)) if actual else []
        passed = actual == expected
        section_sequence_pass = section_sequence_pass and passed
        section_sequences.append(
            {
                "chapter": chapter_number,
                "actual": actual,
                "expected": expected,
                "pass": passed,
            }
        )

    cross_chapter_errors = [
        item
        for item in sections
        if item["containing_chapter"] != item["chapter"]
    ] + [
        item
        for item in deep_sections
        if item["containing_chapter"] != int(str(item["number"]).split(".", 1)[0])
    ]

    appendix_a = [
        item
        for item in appendices
        if re.fullmatch(r"附录\s*A\s*[·・]?\s*变更记录（全量）", str(item["title"]))
    ]
    appendix_is_last_level2 = bool(appendix_a) and all_level2[-1]["line"] == appendix_a[0]["line"]
    appendix_after_last_chapter = bool(appendix_a) and appendix_a[0]["line"] > max(
        (int(item["line"]) for item in chapters), default=0
    )
    appendix_pass = (
        len(appendices) == 1
        and len(appendix_a) == 1
        and appendix_is_last_level2
        and appendix_after_last_chapter
    )

    pending_re = re.compile(r"待填|待裁决|未定|暂定|TBD|待补", re.IGNORECASE)
    pending: list[dict[str, object]] = []
    for index, raw in enumerate(lines):
        line = raw.rstrip("\r\n")
        for match in pending_re.finditer(line):
            token = match.group(0)
            category, reason = classify_pending(
                lines,
                index,
                token,
                appendix_history=bool(appendix_a)
                and index + 1 >= int(appendix_a[0]["line"]),
            )
            pending.append(
                {
                    "line": index + 1,
                    "token": token,
                    "text": line,
                    "context": [
                        {
                            "line": context_index + 1,
                            "text": lines[context_index].rstrip("\r\n"),
                        }
                        for context_index in range(
                            max(0, index - 2), min(len(lines), index + 3)
                        )
                    ],
                    "category": category,
                    "reason": reason,
                }
            )
    untriaged = [item for item in pending if item["category"] == "无解释待定"]

    code_fence_lines = [
        line_no
        for line_no, raw in enumerate(lines, 1)
        if re.match(r"^\s*```", raw.rstrip("\r\n"))
    ]
    code_fence_unclosed = len(code_fence_lines) % 2

    eighteen = [item for item in sections if item["chapter"] == 18]
    chapter_19 = next((item for item in chapters if item["number"] == 19), None)
    eighteen_continuity = {
        "actual": [item["section"] for item in eighteen],
        "lines": [item["line"] for item in eighteen],
        "range": [eighteen[0]["line"], eighteen[-1]["line"]] if eighteen else None,
        "chapter_19_line": chapter_19["line"] if chapter_19 else None,
        "first_level2_after_18_8": next(
            (
                item
                for item in all_level2
                if eighteen and item["line"] > eighteen[-1]["line"]
            ),
            None,
        ),
        "pass": bool(eighteen)
        and [item["section"] for item in eighteen] == list(range(1, 9))
        and chapter_19 is not None
        and next(
            (
                item["line"]
                for item in all_level2
                if item["line"] > eighteen[-1]["line"]
            ),
            None,
        )
        == chapter_19["line"],
    }

    gates = {
        "chapter_sequence": chapter_sequence_pass,
        "section_sequences": section_sequence_pass,
        "cross_chapter_placement": len(cross_chapter_errors) == 0,
        "appendix": appendix_pass,
        "code_fences": code_fence_unclosed == 0,
        "section_18_continuity": eighteen_continuity["pass"],
    }
    result = {
        "source": SOURCE.relative_to(ROOT).as_posix(),
        "sha256_utf8_text": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "line_count": len(lines),
        "eol": {"style": eol, "crlf": crlf, "lf": lf, "cr": cr},
        "chapters": chapters,
        "chapter_numbers": chapter_numbers,
        "all_level2": all_level2,
        "all_level3": all_level3,
        "sections": sections,
        "deep_sections": deep_sections,
        "section_sequences": section_sequences,
        "cross_chapter_errors": cross_chapter_errors,
        "appendix": appendices,
        "appendix_a": appendix_a,
        "pending": pending,
        "untriaged": untriaged,
        "code_fences": {"count": len(code_fence_lines), "lines": code_fence_lines},
        "cmt_unclosed": code_fence_unclosed,
        "section_18": eighteen_continuity,
        "gates": gates,
        "gate_pass": all(gates.values()),
    }
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(
        "chapters={} sections={} appendix={} untriaged={} cmt_unclosed={}".format(
            len(chapters),
            len(sections),
            len(appendices),
            len(untriaged),
            code_fence_unclosed,
        )
    )
    print("chapter_numbers=" + ",".join(str(number) for number in chapter_numbers))
    print("section_18=" + ",".join(f"18.{item['section']}@L{item['line']}" for item in eighteen))
    print("gates=" + json.dumps(gates, ensure_ascii=False, sort_keys=True))
    if untriaged:
        print("untriaged_lines=" + ",".join(str(item["line"]) for item in untriaged))
    return 0 if result["gate_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
