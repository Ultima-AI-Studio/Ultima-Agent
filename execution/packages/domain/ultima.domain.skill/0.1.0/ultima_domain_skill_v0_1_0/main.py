"""Minimal deterministic L2 domain resolver."""

from __future__ import annotations


class DomainSkillPlugin:
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
        return self.domain_resolve({"intent": "task.status.query"})["domain"] == "task"

    def domain_resolve(self, intent):
        intent_name = intent.get("intent") if isinstance(intent, dict) else str(intent)
        return {
            "domain": "task" if intent_name == "task.status.query" else "unknown",
            "intent": intent_name,
            "capabilities": ["task.status.read"] if intent_name == "task.status.query" else [],
        }


def create_plugin() -> DomainSkillPlugin:
    return DomainSkillPlugin()
