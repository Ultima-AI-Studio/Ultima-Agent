#!/usr/bin/env python3
"""Read-only structural and taxonomy audit for the Next architecture tree."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
TREE = ROOT / "docs/tracker/北极星架构树.html"
BASELINE = ROOT / "docs/specs/next-感知交互参数基线-20261113.md"
INVENTORY = ROOT / "docs/plans/next-基础能力盘点与缺口清单-20261113.md"
DUAL_DOMAIN = ROOT / "docs/specs/next-双域分离与开工设置规范.md"
REGISTRATION = ROOT / "docs/plans/next-注册分类-tools-skills-plugins-20261113.md"
OUTPUT = Path(__file__).with_name("tree.json")


def read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def line_of(text: str, fragment: str) -> int | None:
    for line_no, line in enumerate(text.splitlines(), 1):
        if fragment in line:
            return line_no
    return None


class NodeTreeParser(HTMLParser):
    """Parse li.node hierarchy with the li nesting stack as the parent source."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.nodes: list[dict[str, object]] = []
        self.node_stack: list[int] = []
        self.li_stack: list[int | None] = []
        self.capture: tuple[int, str] | None = None
        self.capture_depth = 0
        self.capture_parts: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attr = {key: value or "" for key, value in attrs}
        if tag == "li":
            classes = set(attr.get("class", "").split())
            if "node" in classes:
                node_id = len(self.nodes)
                parent_id = self.node_stack[-1] if self.node_stack else None
                self.nodes.append(
                    {
                        "id": node_id,
                        "parent_id": parent_id,
                        "classes": sorted(classes),
                        "name": "",
                        "description": "",
                    }
                )
                self.node_stack.append(node_id)
                self.li_stack.append(node_id)
            else:
                self.li_stack.append(None)
            return

        if tag == "span" and self.node_stack:
            classes = set(attr.get("class", "").split())
            field = "name" if "name" in classes else "description" if "desc" in classes else None
            if field is not None and self.capture is None:
                self.capture = (self.node_stack[-1], field)
                self.capture_depth = 1
                self.capture_parts = []
                return

        if self.capture is not None:
            self.capture_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self.capture is not None:
            self.capture_depth -= 1
            if self.capture_depth == 0:
                node_id, field = self.capture
                self.nodes[node_id][field] = normalized("".join(self.capture_parts))
                self.capture = None
                self.capture_parts = []

        if tag == "li":
            if not self.li_stack:
                self.errors.append("closing </li> without matching parser stack entry")
                return
            node_id = self.li_stack.pop()
            if node_id is not None:
                if not self.node_stack or self.node_stack[-1] != node_id:
                    self.errors.append(
                        f"li.node stack mismatch at close: expected={node_id} "
                        f"actual={self.node_stack[-1] if self.node_stack else None}"
                    )
                elif self.node_stack:
                    self.node_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.capture is not None:
            self.capture_parts.append(data)

    def close(self) -> None:
        super().close()
        if self.capture is not None:
            self.errors.append("text capture remained open at EOF")
        if self.li_stack:
            self.errors.append(f"li parser stack remained open at EOF: {len(self.li_stack)}")
        if self.node_stack:
            self.errors.append(
                f"li.node parser stack remained open at EOF: {len(self.node_stack)}"
            )


def main() -> int:
    tree_text = read_text(TREE)
    baseline_text = read_text(BASELINE)
    inventory_text = read_text(INVENTORY)
    dual_text = read_text(DUAL_DOMAIN)
    registration_text = read_text(REGISTRATION)

    parser = NodeTreeParser()
    parser.feed(tree_text)
    parser.close()
    nodes = parser.nodes

    by_name: dict[str, list[dict[str, object]]] = {}
    for node in nodes:
        by_name.setdefault(str(node["name"]), []).append(node)

    def get_one(name: str) -> dict[str, object]:
        found = by_name.get(name, [])
        if len(found) != 1:
            raise ValueError(f"expected one node named {name!r}, got {len(found)}")
        return found[0]

    def get_one_under(name: str, parent: dict[str, object]) -> dict[str, object]:
        found = [
            node
            for node in by_name.get(name, [])
            if node["parent_id"] == parent["id"]
        ]
        if len(found) != 1:
            raise ValueError(
                f"expected one node named {name!r} under {parent['name']!r}, "
                f"got {len(found)}"
            )
        return found[0]

    def ancestors(node: dict[str, object], include_self: bool = True) -> list[dict[str, object]]:
        chain: list[dict[str, object]] = [node] if include_self else []
        parent_id = node["parent_id"]
        while parent_id is not None:
            parent = nodes[int(parent_id)]
            chain.append(parent)
            parent_id = parent["parent_id"]
        chain.reverse()
        return chain

    def chain_names(node: dict[str, object]) -> list[str]:
        return [str(item["name"]) for item in ancestors(node)]

    def direct_children(node: dict[str, object]) -> list[dict[str, object]]:
        return [item for item in nodes if item["parent_id"] == node["id"]]

    def descendants(node: dict[str, object]) -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        pending = list(direct_children(node))
        while pending:
            item = pending.pop(0)
            result.append(item)
            pending[0:0] = direct_children(item)
        return result

    tag_counts = {
        "ul": {
            "open": len(re.findall(r"<ul\b", tree_text, re.IGNORECASE)),
            "close": len(re.findall(r"</ul\s*>", tree_text, re.IGNORECASE)),
        },
        "li": {
            "open": len(re.findall(r"<li\b", tree_text, re.IGNORECASE)),
            "close": len(re.findall(r"</li\s*>", tree_text, re.IGNORECASE)),
        },
        "div": {
            "open": len(re.findall(r"<div\b", tree_text, re.IGNORECASE)),
            "close": len(re.findall(r"</div\s*>", tree_text, re.IGNORECASE)),
        },
    }
    for counts in tag_counts.values():
        counts["difference"] = counts["open"] - counts["close"]

    raw_node_count = len(
        re.findall(
            r"<li\b[^>]*class\s*=\s*['\"][^'\"]*\bnode\b[^'\"]*['\"]",
            tree_text,
            re.IGNORECASE,
        )
    )

    p1_node = get_one("主脑（可替换推理后端）")
    p1_chain = chain_names(p1_node)
    p1_expected = [
        "UltimaAgent 本体",
        "UltimaAgent 引擎",
        "基础能力（本体承载）",
        "1. Core（编排与裁决）",
        "主脑（可替换推理后端）",
    ]
    p1 = {
        "node": str(p1_node["name"]),
        "chain": p1_chain,
        "chain_string": " → ".join(p1_chain),
        "depth": len(p1_chain),
        "not_under_capability_group": "能力" not in p1_chain,
        "pass": p1_chain == p1_expected,
    }

    governance = get_one("＋ 治理与约束（⑤）")
    behavior = get_one("行为学原则（五条 · 按人类生物特质）")
    principle_names = [
        "感官分工（通道分工）",
        "理解先于行动",
        "复述确认",
        "记忆分层",
        "不打扰与反馈闭环",
    ]
    p2_items: list[dict[str, object]] = []
    for name in principle_names:
        node = get_one_under(name, behavior)
        chain = chain_names(node)
        passed = (
            governance["id"] in [item["id"] for item in ancestors(node, False)]
            and behavior["id"] in [item["id"] for item in ancestors(node, False)]
            and node["parent_id"] == behavior["id"]
            and governance["parent_id"] == get_one("基础能力（本体承载）")["id"]
        )
        p2_items.append(
            {
                "node": name,
                "chain": chain,
                "chain_string": " → ".join(chain),
                "depth": len(chain),
                "pass": passed,
            }
        )
    p2 = {
        "governance_chain": " → ".join(chain_names(governance)),
        "behavior_chain": " → ".join(chain_names(behavior)),
        "principles": p2_items,
        "pass": len(p2_items) == 5 and all(bool(item["pass"]) for item in p2_items),
    }

    external = get_one("外部能力（容器 · 三抽屉）")
    drawer_names = ["能力库 Skill", "插件 Plugin", "模型库 Provider"]
    external_children = [str(item["name"]) for item in direct_children(external)]
    provider = get_one("模型库 Provider")
    provider_descendants = [str(item["name"]) for item in descendants(provider)]
    positive_mainbrain_entries = [
        name
        for name in provider_descendants
        if "主脑" in name and "不进模型库" not in name
    ]
    p3 = {
        "container_chain": " → ".join(chain_names(external)),
        "direct_children": external_children,
        "expected_drawers": drawer_names,
        "provider_descendants": provider_descendants,
        "positive_mainbrain_entries": positive_mainbrain_entries,
        "mainbrain_policy_nodes": [
            name for name in provider_descendants if "主脑不进模型库" in name
        ],
        "pass": external_children == drawer_names and not positive_mainbrain_entries,
    }

    task_library = get_one("任务库（项目→工单卡→任务→运行实例）")
    log_library = get_one("日志库（审计与留痕）")
    p4 = {
        "task_library_chain": " → ".join(chain_names(task_library)),
        "task_library_parent": str(nodes[int(task_library["parent_id"])]["name"]),
        "log_library_chain": " → ".join(chain_names(log_library)),
        "log_library_parent": str(nodes[int(log_library["parent_id"])]["name"]),
        "pass": (
            task_library["parent_id"] == get_one("＋ Console（引擎中心管理调度器）")["id"]
            and log_library["parent_id"] == governance["id"]
        ),
    }

    memory_tool = get_one("writer · poison_guard · store_backend · temperature_tier · volumes")
    memory_desc = str(memory_tool["description"])
    p5_checks = {
        "hot_500mb": bool(re.search(r"热\s*500\s*MB", memory_desc, re.IGNORECASE)),
        "warm_2gb": bool(re.search(r"温\s*2\s*GB", memory_desc, re.IGNORECASE)),
        "fixed_value": "定值" in memory_desc,
        "cold_path_configurable": "冷层存档路径可指定" in memory_desc,
    }
    p5 = {
        "node": str(memory_tool["name"]),
        "chain": " → ".join(chain_names(memory_tool)),
        "description": memory_desc,
        "checks": p5_checks,
        "pass": all(p5_checks.values()),
    }

    basic = get_one("基础能力（本体承载）")
    delivery = get_one("交付（远程更新与安装交付）")
    b_expected_basic = [
        "1. Core（编排与裁决）",
        "2. Senses.Voice（语音进出）",
        "3. Shell（进程治理）",
        "4. Surface（界面与呈现）",
        "5. Memory（记忆与自学习）",
        "6. Middleware（执行端与票据）",
    ]
    b_expected_delivery = [
        "7. Update（远程更新）",
        "8. Lifecycle（安装与交付）",
    ]
    basic_children = [str(item["name"]) for item in direct_children(basic)]
    delivery_children = [str(item["name"]) for item in direct_children(delivery)]

    a_expected = [
        "基础能力（本体承载）",
        "外部能力（容器 · 三抽屉）",
        "交付（远程更新与安装交付）",
    ]
    engine = get_one("UltimaAgent 引擎")
    engine_children = [str(item["name"]) for item in direct_children(engine)]
    rendered_categories = [name for name in engine_children if name in a_expected]

    c_expected = [
        "① 感知与交互",
        "② 语音",
        "③ 理解与决策",
        "④ 宿主、执行与编排",
        "⑤ 治理与约束",
        "⑥ 记忆与自学习",
        "⑧ 交付（Update / Lifecycle)",
    ]
    registration_heading_matches = []
    for line_no, line in enumerate(registration_text.splitlines(), 1):
        match = re.match(r"^###\s+(.+)$", line)
        if match and any(match.group(1).startswith(prefix[:2]) for prefix in c_expected):
            registration_heading_matches.append(
                {"line": line_no, "heading": match.group(1)}
            )

    taxonomies = {
        "A_presentation_three_categories": {
            "definition_count": len(
                re.findall(r"^####\s+1\.1\.1\s+呈现层级（三类", inventory_text, re.MULTILINE)
            ),
            "definition": {
                "file": INVENTORY.relative_to(ROOT).as_posix(),
                "line": line_of(inventory_text, "#### 1.1.1 呈现层级（三类"),
            },
            "baseline_reference": {
                "line": line_of(baseline_text, "呈现层级因此从**五类塌成三类**"),
                "text": "基础能力 / 外部能力 / 交付",
            },
            "tree_rendered_categories": rendered_categories,
            "tree_other_engine_children": [
                name for name in engine_children if name not in a_expected
            ],
            "conflicts": [],
            "pass": rendered_categories == a_expected,
        },
        "B_engineering_eight_blocks": {
            "definition_count": len(
                re.findall(r"^##\s+七、八模块的具体设置基线", dual_text, re.MULTILINE)
            ),
            "definition": {
                "file": DUAL_DOMAIN.relative_to(ROOT).as_posix(),
                "line": line_of(dual_text, "## 七、八模块的具体设置基线"),
            },
            "inventory_reference_line": line_of(
                inventory_text, "**B 工程模块（八块）**"
            ),
            "tree_basic_blocks": [name for name in basic_children if name in b_expected_basic],
            "tree_delivery_blocks": [
                name for name in delivery_children if name in b_expected_delivery
            ],
            "expected_basic_blocks": b_expected_basic,
            "expected_delivery_blocks": b_expected_delivery,
            "conflicts": [],
            "pass": (
                [name for name in basic_children if name in b_expected_basic]
                == b_expected_basic
                and [name for name in delivery_children if name in b_expected_delivery]
                == b_expected_delivery
            ),
        },
        "C_functional_seven_buckets": {
            "definition_count": len(
                re.findall(r"^###\s+1\.1\s+模块口径对照", inventory_text, re.MULTILINE)
            ),
            "definition": {
                "file": INVENTORY.relative_to(ROOT).as_posix(),
                "line": line_of(inventory_text, "### 1.1 模块口径对照"),
                "bucket_lines": list(range(21, 28)),
            },
            "registration_rendering": registration_heading_matches,
            "conflicts": [],
            "pass": (
                len(registration_heading_matches) == 7
                and [item["heading"] for item in registration_heading_matches]
                == [
                    "① 感知与交互（终端 4IO / 输出呈现 / 交互循环 / 表达与总结）",
                    "② 语音（KWS / ASR / TTS / CV3 音色训练）",
                    "③ 理解与决策（意图理解 / 领域知识与技能注册）",
                    "④ 宿主、执行与编排（执行与外部接入 / 编排与组合窗口 / Console 任务中枢 / 进程治理）",
                    "⑤ 治理与约束（行为约束 / 范式引擎 / 权威源）",
                    "⑥ 记忆与自学习（记忆与自学习）",
                    "⑧ 交付（Update / Lifecycle）",
                ]
            ),
        },
    }
    taxonomy_conflict_count = sum(
        len(item["conflicts"]) for item in taxonomies.values()
    )

    nodes_for_output = []
    for node in nodes:
        nodes_for_output.append(
            {
                **node,
                "chain": chain_names(node),
                "chain_string": " → ".join(chain_names(node)),
                "depth": len(chain_names(node)),
            }
        )

    gates = {
        "node_count_113": len(nodes) == 113 and raw_node_count == 113,
        "tag_balance": all(counts["difference"] == 0 for counts in tag_counts.values()),
        "parser_stack": not parser.errors,
        "p1": bool(p1["pass"]),
        "p2": bool(p2["pass"]),
        "p3": bool(p3["pass"]),
        "p4": bool(p4["pass"]),
        "p5": bool(p5["pass"]),
        "taxonomy_definitions": all(
            item["definition_count"] == 1 for item in taxonomies.values()
        ),
        "taxonomy_consistency": (
            taxonomy_conflict_count == 0
            and all(bool(item["pass"]) for item in taxonomies.values())
        ),
    }

    result = {
        "source": TREE.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(tree_text.encode("utf-8")).hexdigest(),
        "node_count": len(nodes),
        "raw_li_node_count": raw_node_count,
        "tag_counts": tag_counts,
        "parser_errors": parser.errors,
        "nodes": nodes_for_output,
        "P1": p1,
        "P2": p2,
        "P3": p3,
        "P4": p4,
        "P5": p5,
        "taxonomies": taxonomies,
        "taxonomy_conflict_count": taxonomy_conflict_count,
        "gates": gates,
        "gate_pass": all(gates.values()),
    }
    with OUTPUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(
        f"nodes={len(nodes)} raw_nodes={raw_node_count} "
        f"ul={tag_counts['ul']['open']}/{tag_counts['ul']['close']} "
        f"li={tag_counts['li']['open']}/{tag_counts['li']['close']} "
        f"div={tag_counts['div']['open']}/{tag_counts['div']['close']}"
    )
    print(f"P1={p1['chain_string']} depth={p1['depth']}")
    print(f"P2_principles={len(p2_items)} P3_drawers={len(external_children)}")
    print(f"taxonomy_conflicts={taxonomy_conflict_count} gates={json.dumps(gates, ensure_ascii=False, sort_keys=True)}")
    return 0 if result["gate_pass"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, ValueError) as error:
        print(f"audit_tree_error={error}", file=sys.stderr)
        raise SystemExit(2)
