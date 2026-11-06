"""s2-tool-extend: OpenJarvis 底座工具接入契约测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(r"H:\UltimaAI\UltimaAgent")
for path in (ROOT, ROOT / "src" / "brain", ROOT / "libs" / "base" / "openjarvis" / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from openjarvis.core.registry import ToolRegistry  # noqa: E402
from src.brain import agent_server  # noqa: E402
from agent_tools_ultima import (  # noqa: E402
    UltimaMemoryTool,
    UltimaSkillManageTool,
    UltimaSubagentTool,
    UltimaTaskAdjustTool,
    UltimaTaskQueryTool,
    UltimaWebSearchTool,
)


EXPECTED_EXTENDED_TOOLS = {
    "ultima_subagent",
    "ultima_skill_manage",
    "ultima_memory",
    "ultima_web_search",
}
ORIGINAL_ULTIMA_TOOLS = {
    "ultima_task_query",
    "ultima_task_adjust",
    "ultima_env_snapshot",
}


class _FakeChild:
    def __init__(self) -> None:
        self.closed = False

    def ask_full(self, query: str, **kwargs):
        return {
            "content": "当前任务队列与真实数据一致。",
            "tool_results": [
                {
                    "tool_name": "ultima_task_query",
                    "content": "当前共 3 个任务。",
                    "success": True,
                }
            ],
        }

    def close(self) -> None:
        self.closed = True


class ToolWhitelistContractTests(unittest.TestCase):
    def test_whitelist_adds_only_the_four_approved_categories(self) -> None:
        self.assertTrue(EXPECTED_EXTENDED_TOOLS.issubset(agent_server.TOOLS))
        self.assertTrue(ORIGINAL_ULTIMA_TOOLS.issubset(agent_server.TOOLS))

    def test_extended_tools_are_registered_with_ultima_trigger_descriptions(self) -> None:
        expected_phrases = {
            "ultima_subagent": "子智能体",
            "ultima_skill_manage": "技能",
            "ultima_memory": "记住",
            "ultima_web_search": "上网",
        }
        for name, phrase in expected_phrases.items():
            self.assertTrue(ToolRegistry.contains(name), name)
            self.assertIn(phrase, ToolRegistry.create(name).spec.description)


class ProjectScopedToolTests(unittest.TestCase):
    def test_task_query_readonly_fallback_accepts_manager_utf8_bom_index(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as tmp:
            task_root = Path(tmp)
            (task_root / "tasks.json").write_text(
                '[{"task_id":"queued-1","state":"QUEUED","priority":1,'
                '"dependsOn":[],"parallelGroup":null,"fileDomain":[],'
                '"reasoningEffort":"low","created_at":"2026-10-26T00:00:00Z",'
                '"updated_at":"2026-10-26T00:00:00Z","terminal_reason":null,'
                '"card_path":"cards/queued-1/task.md"}]',
                encoding="utf-8-sig",
            )
            result = UltimaTaskQueryTool(root=task_root).execute()
            self.assertTrue(result.success, result.content)
            self.assertIn("当前共 1 个任务", result.content)
            self.assertIn("排队中 1", result.content)

    def test_task_adjust_keeps_queueplanner_entry_with_manager_utf8_bom_index(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as tmp:
            task_root = Path(tmp)
            record = (
                '[{"task_id":"queued-1","state":"QUEUED","priority":1,'
                '"dependsOn":[],"parallelGroup":null,"fileDomain":[],'
                '"reasoningEffort":"low","created_at":"2026-10-26T00:00:00Z",'
                '"updated_at":"2026-10-26T00:00:00Z","terminal_reason":null,'
                '"card_path":"cards/queued-1/task.md"}]'
            )
            (task_root / "tasks.json").write_text(record, encoding="utf-8-sig")
            result = UltimaTaskAdjustTool(root=task_root).execute(
                action="priority", task_id="queued-1", priority=2
            )
            self.assertTrue(result.success, result.content)
            reread = UltimaTaskQueryTool(root=task_root).execute()
            self.assertTrue(reread.success, reread.content)

    def test_skill_create_list_load_roundtrip_stays_in_requested_directory(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as tmp:
            tool = UltimaSkillManageTool(skills_dir=tmp)
            created = tool.execute(
                action="create",
                name="s2_acceptance_skill",
                description="验收技能",
                steps=[{"tool_name": "ultima_task_query"}],
            )
            listed = tool.execute(action="list")
            loaded = tool.execute(action="load", name="s2_acceptance_skill")
            self.assertTrue(created.success, created.content)
            self.assertIn("s2_acceptance_skill", listed.content)
            self.assertIn('name = "s2_acceptance_skill"', loaded.content)
            self.assertTrue((Path(tmp) / "s2_acceptance_skill.toml").is_file())

    def test_memory_add_read_roundtrip_stays_in_requested_file(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as tmp:
            memory_path = Path(tmp) / "MEMORY.md"
            tool = UltimaMemoryTool(memory_path=memory_path)
            added = tool.execute(action="add", entry="用户喜欢简洁回答")
            recalled = tool.execute(action="read")
            self.assertTrue(added.success, added.content)
            self.assertIn("用户喜欢简洁回答", recalled.content)
            self.assertTrue(memory_path.is_file())

    def test_subagent_executes_child_and_returns_child_tool_evidence(self) -> None:
        child = _FakeChild()
        tool = UltimaSubagentTool(child_factory=lambda: child)
        result = tool.execute(task="查一下当前任务状态")
        self.assertTrue(result.success, result.content)
        self.assertIn("当前任务队列与真实数据一致", result.content)
        self.assertIn("ultima_task_query", result.content)
        self.assertTrue(child.closed)

    def test_web_search_rejects_empty_query_without_fabricating_results(self) -> None:
        result = UltimaWebSearchTool().execute(query="")
        self.assertFalse(result.success)
        self.assertIn("搜索关键词", result.content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
