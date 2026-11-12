"""Adapter over the frozen v0.3 task-status intent behavior."""

from __future__ import annotations

from dataclasses import asdict

from src.brain.intent import parse_task_status_intent


class IntentRulePlugin:
    def load(self) -> None:
        pass

    def activate(self) -> None:
        pass

    def disable(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def smoke(self) -> bool:
        return parse_task_status_intent("请查一下任务状态").matched

    def intent_parse(self, text, sessionId):
        result = asdict(parse_task_status_intent(text))
        result["sessionId"] = sessionId
        return result


def create_plugin() -> IntentRulePlugin:
    return IntentRulePlugin()
