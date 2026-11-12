"""L8 安全护栏拼装层（M2）。

接线范式（对齐 tech-progression-plan §2）：
1. 接口对齐：实现 openjarvis.security._stubs.BaseScanner（scan/redact）
2. 注册接入：注册进 GuardrailsRegistry，key="nemo_guardrails"
3. 驻留标记：fail-closed，注册后拒绝热卸载（residency 硬约束）
4. 白名单：tools 白名单由 UltimaAgent 配置统一管控，未授权工具一律拒绝
5. 锁版本：nemoguardrails 0.24.1 已入 wheels 缓存，锁版本 vendor

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from .registry import GuardrailsRegistry, ResidencyViolationError
from .scanner import NeMoScanner, ScanOutcome
from .policy import CapabilityPolicy
from .credentials import (
    CredentialCenter,
    CredentialError,
    CredentialNotFound,
    MissingSecret,
    SecretEntry,
    SecretValue,
    redact,
    scrub_log_text,
    get_credential_center,
)
from .hazard import (
    HazardGate,
    HazardGateError,
    OperationSpec,
    AuthorizationDecision,
)
from .scope import ScopePolicy, ScopeDecision, parse_scope, DEV_SCOPES
from .adjudicate import (
    AdjudicationTable,
    AdjudicationDecision,
    REDLINES,
    HAZARDS,
)
from .paradigm import (
    ParadigmGate,
    ParadigmDecision,
    FLOW_RINGS,
    RING_INDEX,
)
from .audit_log import AppendOnlyAuditLog, AuditEntry, AuditLogError
from .receipt import ReceiptValidator, ReceiptResult, ReceiptIssue
from .reviewer import (
    IndependentReviewer,
    ReviewResult,
    Finding,
    ReviewError,
    AUDIT_ROLES,
    SEVERITIES,
)

__all__ = [
    "GuardrailsRegistry",
    "ResidencyViolationError",
    "NeMoScanner",
    "ScanOutcome",
    "CapabilityPolicy",
    "CredentialCenter",
    "CredentialError",
    "CredentialNotFound",
    "MissingSecret",
    "SecretEntry",
    "SecretValue",
    "redact",
    "scrub_log_text",
    "get_credential_center",
    "HazardGate",
    "HazardGateError",
    "OperationSpec",
    "AuthorizationDecision",
    "ScopePolicy",
    "ScopeDecision",
    "parse_scope",
    "DEV_SCOPES",
    "AdjudicationTable",
    "AdjudicationDecision",
    "REDLINES",
    "HAZARDS",
    "ParadigmGate",
    "ParadigmDecision",
    "FLOW_RINGS",
    "RING_INDEX",
    "AppendOnlyAuditLog",
    "AuditEntry",
    "AuditLogError",
    "ReceiptValidator",
    "ReceiptResult",
    "ReceiptIssue",
    "IndependentReviewer",
    "ReviewResult",
    "Finding",
    "ReviewError",
    "AUDIT_ROLES",
    "SEVERITIES",
]
