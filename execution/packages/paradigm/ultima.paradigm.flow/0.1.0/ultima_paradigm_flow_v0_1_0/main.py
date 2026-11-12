"""L10 范式闸门总线插件（M26：paradigm.run）。

承载 7 环流程强制检查（意图→领域→排版→样式→动效→呈现→汇报）+ 防直达能力。
复用既有 L10 组件（ParadigmGate）+ LangGraphStateMachine（M4 拼装），
不另造体系；本包仅做总线适配壳。

- paradigm.run(flowId, input)：
    input 须声明 step（当前环名）与 target（目标能力）。
    1. ParadigmGate.advance 环环相扣推进（跳环/回退/重复拒绝）
    2. target 为对外交付（present/report/exec 等）时，assert_complete 强制 7 环全绿
- 强制驻留：总线 L10 域硬约束（unload/disable 拒绝）。
"""

from __future__ import annotations

from pathlib import Path

_AUDIT_PATH = Path(__file__).resolve().parents[4] / "logs" / "paradigm-audit.jsonl"


class ParadigmFlowPlugin:
    def load(self) -> None:
        from src.brain.guardrails import ParadigmGate

        self._gate = ParadigmGate(audit_path=str(_AUDIT_PATH))

    def activate(self) -> None:
        pass

    def disable(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def smoke(self) -> bool:
        if self._gate is None:
            return False
        # 防直达：未走任何环的 flow 请求对外交付必须被拒 = 闸门生效
        d = self._gate.assert_complete("__smoke_probe__")
        return not d.allowed

    def paradigm_run(self, flowId: str, input):
        """paradigm.run(flowId, input) —— 7 环流程强制检查。

        input 结构：
            {
              "step": "intent|domain|layout|style|motion|present|report"（或中文环名）,
              "target": "对外交付目标（present/report/exec.run 等，可选）
            }
        """
        if not isinstance(input, dict):
            return {
                "verdict": "deny",
                "reason": "input 必须是对象（含 step 声明）",
                "flowId": flowId,
            }
        # 惰性初始化：总线 call 现场建实例时保证组件就绪（幂等）
        if not hasattr(self, "_gate"):
            self.load()
        step = input.get("step")
        if not step:
            return {
                "verdict": "deny",
                "reason": "缺少 step 声明（7 环流程强制检查）",
                "flowId": flowId,
            }
        # 环环相扣推进
        adv = self._gate.advance(flowId, step)
        if not adv.allowed:
            return {
                "verdict": "deny",
                "reason": adv.reason,
                "passed_rings": list(adv.passed_rings),
                "flowId": flowId,
            }
        # 防直达能力：对外交付前必须 7 环全绿
        target = input.get("target", "")
        if target:
            gate = self._gate.assert_complete(flowId, target=target)
            if not gate.allowed:
                return {
                    "verdict": "deny",
                    "reason": gate.reason,
                    "passed_rings": list(gate.passed_rings),
                    "flowId": flowId,
                }
        return {
            "verdict": "allow",
            "step": step,
            "completed": adv.completed,
            "passed_rings": list(adv.passed_rings),
            "flowId": flowId,
        }


def create_plugin() -> ParadigmFlowPlugin:
    return ParadigmFlowPlugin()
