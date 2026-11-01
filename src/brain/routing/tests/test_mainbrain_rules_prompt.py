from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

from src.brain import agent_server
from openjarvis.agents.native_react import NativeReActAgent
from openjarvis.core.types import Role


def test_startup_prompt_combines_jarvis_and_authoritative_rule_block() -> None:
    baseline = agent_server.MAINBRAIN_RULES_PATH.read_text(encoding="utf-8")
    rules = baseline.split("```", 2)[1].strip()
    persona = agent_server.JARVIS_PERSONA_PATH.read_text(encoding="utf-8").strip()
    assert persona in agent_server.MAINBRAIN_SYSTEM_PROMPT
    assert rules in agent_server.MAINBRAIN_SYSTEM_PROMPT
    assert "【回答规则】" in agent_server.MAINBRAIN_SYSTEM_PROMPT
    assert "【行为规则】" in agent_server.MAINBRAIN_SYSTEM_PROMPT


def test_agent_server_keeps_user_question_separate(monkeypatch) -> None:
    jarvis = Mock()
    jarvis.ask_full.side_effect = [
        {"content": "第一轮。", "tool_results": [], "usage": {}},
        {"content": "第二轮。", "tool_results": [], "usage": {}},
    ]
    monkeypatch.setattr(agent_server, "get_jarvis", lambda: jarvis)
    monkeypatch.setattr(agent_server, "EVENT_BUS", Mock())
    with patch.object(Path, "read_text", side_effect=AssertionError("per-turn read")):
        agent_server.ask_once("第一问")
        agent_server.ask_once("第二问")
    assert jarvis.ask_full.call_count == 2
    for call, question in zip(jarvis.ask_full.call_args_list, ("第一问", "第二问"), strict=True):
        assert call.args[0] == question


def test_every_native_react_turn_has_cached_rules_in_system_message() -> None:
    agent = NativeReActAgent(Mock(), "test-model", tools=[])
    captured = []

    def generate(messages):
        captured.append(messages)
        return {"content": "Final Answer: 正常回答。", "usage": {}}

    agent._generate = generate
    with patch.object(Path, "read_text", side_effect=AssertionError("per-turn read")):
        agent.run("第一问")
        agent.run("第二问")
    assert len(captured) == 2
    for messages in captured:
        system = next(message for message in messages if message.role is Role.SYSTEM)
        assert agent_server.MAINBRAIN_SYSTEM_PROMPT in system.content
