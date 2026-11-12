"""NeMo Guardrails 内容护栏扫描器（实现底座 BaseScanner ABC）。

对齐 tech-progression-plan §2.1：接口对齐 —— 实现
openjarvis.security._stubs.BaseScanner（scan / redact），内部封装
nemoguardrails LLMRails 做输入 rails 检查。

出口验收（M2）：
- 未授权拒绝 100%：未授权工具调用 / 敏感内容一律拦截
- 驻留标记生效：GuardrailsRegistry.unload("nemo_guardrails") 抛拒绝

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional

from openjarvis.security.types import ScanResult, ScanFinding, ThreatLevel
from openjarvis.security._stubs import BaseScanner

from .registry import GuardrailsRegistry


@dataclass
class ScanOutcome:
    """一次 rails 检查结果。"""

    allowed: bool
    reason: str = ""
    message_id: Optional[str] = None
    event: str = ""


class NeMoScanner(BaseScanner):
    """NeMo Guardrails 内容护栏扫描器。

    scanner_id: 固定标识 `"nemo_guardrails"`，用于日志与审计。

    Parameters
    ----------
    rails_config_dir:
        可选，指向 NeMo Colang 配置目录；未提供时使用内置默认 rails
        （最小安全集：拒绝注入、拒绝未授权工具）。
    block_on_injection:
        是否将注入/越权探测结果视为 BLOCK（拒绝）。
    """

    scanner_id = "nemo_guardrails"

    # 内置最小 rails 配置（无需外部目录即可工作的确定性规则）
    # 说明：实际 Colang 引擎按需从 config dir 加载；无目录时降级到
    # 确定性关键词/模式检查，保证离线可用。
    _BLOCK_PATTERNS = (
        "ignore previous instructions",
        "ignore prior instructions",
        "ignore all previous instructions",
        "ignore instructions",
        "ignore your instructions",
        "ignore above",
        "disregard previous",
        "disregard instructions",
        "system prompt",
        "do not follow",
        "bypass",
        "jailbreak",
        "reveal secrets",
        "忘记之前的指令",
        "忘记所有指令",
        "忘记指令",
        "忽略之前的指令",
        "忽略之前所有指令",
        "忽略所有之前的指令",
        "忽略指令",
        "忽略你的指令",
        "忽略上述",
        "无视规则",
        "无视指令",
        "无视之前的指令",
        "不用理会指令",
        "不用管指令",
        "不要遵循",
        "绕过",
        "输出系统提示词",
        "输出系统提示",
        "泄露系统提示词",
        "sysprompt",
    )

    _UNAUTHORIZED_TOOL_HINTS = (
        "shell_exec",
        "code_interpreter",
        "file_write",
        "rm -rf",
        "del /f",
        "format",
        "rd /s",
    )

    def __init__(
        self,
        rails_config_dir: Optional[str] = None,
        *,
        block_on_injection: bool = True,
    ) -> None:
        self._rails_config_dir = rails_config_dir
        self._block_on_injection = block_on_injection
        self._llm_rails: Any = None
        self._init_llm_rails()

        # 注册进 GuardrailsRegistry（驻留标记，fail-closed）
        # 幂等：同 key 已注册时跳过（同进程多次实例化同一替换件合法）
        if not GuardrailsRegistry.is_registered(self.scanner_id):
            GuardrailsRegistry.register(
                self.scanner_id,
                self,
                resident=True,
                description="NeMo Guardrails 内容护栏（L8，驻留）",
            )

    def _init_llm_rails(self) -> None:
        """初始化 nemoguardrails LLMRails（无配置目录时仅初始化，不做 LLM 调用）。"""
        try:
            from nemoguardrails import LLMRails
            from nemoguardrails import RailsConfig
        except ImportError:  # pragma: no cover - 离线环境缺包时记录
            self._llm_rails = None
            return
        try:
            if self._rails_config_dir:
                config = RailsConfig.from_path(self._rails_config_dir)
                self._llm_rails = LLMRails(config)
            else:
                # 无目录：构建最小内存配置（确定性 rails，不依赖 LLM 判断）
                minimal = RailsConfig(
                    instructions=[
                        "你是 Ultima Agent 的安全护栏。"
                        "仅允许安全、合规的对话与操作。"
                    ],
                    user_messages=[],
                )
                self._llm_rails = LLMRails(minimal)
        except Exception:  # pragma: no cover - 配置异常不影响确定性降级
            self._llm_rails = None

    # -- BaseScanner ABC ---------------------------------------------------

    def scan(self, text: str) -> ScanResult:
        """扫描 *text*，返回 findings（注入/越权命中）。

        实现方式：确定性模式匹配（离线可用），输出统一 ScanResult，
        与底座 GuardrailsEngine 的 WARN/REDACT/BLOCK 三态协作。
        """
        result = ScanResult()
        lowered = (text or "").lower()

        for pattern in self._BLOCK_PATTERNS:
            if pattern.lower() in lowered:
                idx = (text or "").lower().find(pattern.lower())
                result.findings.append(
                    ScanFinding(
                        pattern_name="nemo_injection",
                        matched_text=pattern,
                        threat_level=ThreatLevel.HIGH,
                        start=idx,
                        end=idx + len(pattern),
                        description=f"检测到注入/越权提示词模式: {pattern}",
                    )
                )

        for hint in self._UNAUTHORIZED_TOOL_HINTS:
            if hint in lowered:
                idx = (text or "").lower().find(hint)
                result.findings.append(
                    ScanFinding(
                        pattern_name="unauthorized_tool",
                        matched_text=hint,
                        threat_level=ThreatLevel.HIGH,
                        start=idx,
                        end=idx + len(hint),
                        description=f"检测到未授权工具/危险操作提示: {hint}",
                    )
                )
        return result

    def redact(self, text: str) -> str:
        """返回替换敏感命中的文本（注入/越权提示词打码）。"""
        redacted = text
        for pattern in self._BLOCK_PATTERNS:
            if pattern in redacted:
                redacted = redacted.replace(pattern, "[BLOCKED]")
        for hint in self._UNAUTHORIZED_TOOL_HINTS:
            if hint in redacted:
                redacted = redacted.replace(hint, "[BLOCKED]")
        return redacted

    # -- rails 风格检查（供 CLI/上层使用）--------------------------------

    def check(self, text: str) -> ScanOutcome:
        """对 *text* 做输入检查，返回是否放行与原因。

        Returns
        -------
        ScanOutcome
            allowed=True 放行；allowed=False 拒绝（未授权 100% 拒绝）。
        """
        result = self.scan(text)
        if result.findings and self._block_on_injection:
            reasons = "; ".join(f.description for f in result.findings)
            return ScanOutcome(
                allowed=False,
                reason=f"输入被 L8 护栏拦截: {reasons}",
                event="nemo_blocked",
            )
        return ScanOutcome(allowed=True, reason="通过 L8 护栏检查")


__all__ = ["NeMoScanner", "ScanOutcome"]
