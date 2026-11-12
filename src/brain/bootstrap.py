"""UltimaAgent 底座运行时接线（bootstrap）。

M6 第二段 G1-G3 闭环的唯一接线入口：把 L8/L9/L10 三件替换件
双登记进底座运行时注册表（openjarvis.core.registry），使
「底座入口（jarvis ask / JarvisSystem）→ L8 → L9 → L10」形成真实链路。

对齐 ADR-011 接线范式：
- 底座注册表 = 运行时取件通道（RegistryBase.create/get）
- 自建注册表 = 驻留/审计/白名单管控通道（src.brain.*.Registry）
- 双登记幂等：注册前先 contains 判断，重复调用不抛错

本模块位于 H:\\UltimaAI\\UltimaAgent\\ 写域内，只写本目录。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)

# 底座注册表键（Ultima 专用，避免与底座默认键冲突）
MEMORY_BACKEND_KEY = "mem0_ultima"
ROUTER_POLICY_KEY = "ultima_langgraph"

_INSTALLED = False

# 底座 setup_security 原函数引用（patch 前缓存，包装版内部调用它，
# 避免取到替换后的自己形成无限递归）
_ORIGINAL_SETUP_SECURITY = None


# ---------------------------------------------------------------------------
# 对外安装入口（幂等）
# ---------------------------------------------------------------------------
def install(config_path: Optional[str] = None) -> bool:
    """一次性挂接三件套到底座注册表。

    Parameters
    ----------
    config_path:
        可选：Ultima 独立配置文件路径。传入时同时注入配置覆盖
        （memory.default_backend / security 段），避免修改 C 盘全局
        config.toml。None 时不改任何配置，仅做注册表接线。

    Returns
    -------
    bool
        True 表示全部接线完成；False 表示存在失败项（见日志）。
    """
    global _INSTALLED
    ok = True
    ok = _register_memory_backend() and ok
    ok = _register_router_policy() and ok
    ok = _patch_setup_security() and ok
    ok = _snapshot_environment() and ok
    ok = _install_skill_whitelist() and ok
    ok = _install_preference_store() and ok
    ok = _install_orb_state_machine() and ok
    if config_path:
        ok = _inject_config(config_path) and ok
    _INSTALLED = ok
    return ok


def is_installed() -> bool:
    """返回接线状态（供测试/审计断言）。"""
    return _INSTALLED


# ---------------------------------------------------------------------------
# P1 · L3 环境认知：启动即环境快照（best-effort，幂等）
# ---------------------------------------------------------------------------
def _snapshot_environment() -> bool:
    """启动时生成环境快照并落盘（P1 补建项，L3 口径）。

    快照目录：<UltimaAgent>/data/environment/snapshot.json
    - best-effort：任何失败只记日志，不阻断 install() 主流程；
    - 幂等：每次 install() 重新抓取（启动即环境快照语义），不重复报错；
    - 落点固定，供 L1 意图补全 / L3 执行接入按契约读取。
    """
    try:
        from src.brain.environment import capture_snapshot, snapshot_to_file

        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        out = root / "data" / "environment" / "snapshot.json"
        snap = capture_snapshot()
        written = snapshot_to_file(snap, str(out))
        logger.info("L3 environment: snapshot written -> %s (%d items)", written, len(snap.to_dict()))
        return True
    except Exception as exc:  # pragma: no cover - best-effort 失败不阻断
        logger.warning("L3 environment: snapshot failed (non-blocking): %s", exc)
        return False


# ---------------------------------------------------------------------------
# G2 · L9 记忆：Mem0Backend → 底座 MemoryRegistry
# ---------------------------------------------------------------------------
def _register_memory_backend() -> bool:
    from openjarvis.core.registry import MemoryRegistry

    if MemoryRegistry.contains(MEMORY_BACKEND_KEY):
        logger.info("G2 memory: '%s' already registered, skip", MEMORY_BACKEND_KEY)
        return True

    from src.brain.memory.backend import Mem0Backend

    MemoryRegistry.register_value(MEMORY_BACKEND_KEY, Mem0Backend)
    logger.info("G2 memory: MemoryRegistry[%s] = Mem0Backend", MEMORY_BACKEND_KEY)
    return MemoryRegistry.contains(MEMORY_BACKEND_KEY)


# ---------------------------------------------------------------------------
# G3 · L10 范式：LangGraphStateMachine → 底座 RouterPolicyRegistry
# ---------------------------------------------------------------------------
def _router_factory(*args: Any, **kwargs: Any) -> Any:
    """RouterPolicyRegistry.create 的工厂适配。

    底座 executor.py L402 以 ``create(key, available_models=...)``
    取件，而 LangGraphStateMachine 构造是 keyword-only
    （engine_key/log_path/auto_approve）。此工厂吸收 available_models
    位置参数，仅把引擎所需参数透传给 LangGraphStateMachine。
    """
    kwargs.pop("available_models", None)
    return _langgraph_cls(**kwargs)


_langgraph_cls: Any = None


def _register_router_policy() -> bool:
    global _langgraph_cls
    from openjarvis.core.registry import RouterPolicyRegistry

    if RouterPolicyRegistry.contains(ROUTER_POLICY_KEY):
        logger.info("G3 router: '%s' already registered, skip", ROUTER_POLICY_KEY)
        return True

    from src.brain.orchestration.engine import LangGraphStateMachine

    _langgraph_cls = LangGraphStateMachine
    RouterPolicyRegistry.register_value(ROUTER_POLICY_KEY, _router_factory)
    logger.info("G3 router: RouterPolicyRegistry[%s] = factory(LangGraphStateMachine)", ROUTER_POLICY_KEY)
    return RouterPolicyRegistry.contains(ROUTER_POLICY_KEY)


# ---------------------------------------------------------------------------
# G1 · L8 安全：NeMoScanner → 底座 GuardrailsEngine 扫描链
# ---------------------------------------------------------------------------
def _ultima_setup_security(config: Any, engine: Any, bus: Any = None) -> Any:
    """包装 openjarvis.security.setup_security，注入 NeMoScanner。

    底座 setup_security 只按 config.security.secret_scanner/pii_scanner
    布尔开关构造 SecretScanner/PIIScanner，无第三方 scanner 挂点。
    本包装：
    1. 先调底座原函数（patch 前缓存的原版引用），拿到已按 config
       包装的 SecurityContext；
    2. 若底座已构造 GuardrailsEngine（security.enabled 且 scanners 非空），
       把 NeMoScanner 追加进其扫描链（去重）；
    3. 若底座因 scanners 全关而未包装（engine 未包 GuardrailsEngine），
       则 Ultima 侧强制包一层 GuardrailsEngine（fail-closed，
       scanners=[NeMoScanner()]，mode=block）。
    """
    from openjarvis.security.guardrails import GuardrailsEngine
    from openjarvis.security.types import RedactionMode

    if _ORIGINAL_SETUP_SECURITY is None:
        raise RuntimeError(
            "bootstrap: _ORIGINAL_SETUP_SECURITY 未缓存，"
            "必须经 _patch_setup_security() 安装包装"
        )
    ctx = _ORIGINAL_SETUP_SECURITY(config, engine, bus)

    if not getattr(config.security, "enabled", False):
        # 安全整体关闭：尊重底座语义，不强制注入（守卫由调用方决定）
        return ctx

    try:
        from src.brain.guardrails.scanner import NeMoScanner
    except Exception as exc:  # pragma: no cover - 依赖缺失降级
        logger.warning("G1 security: NeMoScanner import failed: %s", exc)
        return ctx

    current = getattr(ctx, "engine", None)
    if isinstance(current, GuardrailsEngine):
        scanners = getattr(current, "_scanners", None)
        if scanners is None:
            current._scanners = []
            scanners = current._scanners
        exists = any(getattr(s, "scanner_id", "") == NeMoScanner.scanner_id for s in scanners)
        if not exists:
            scanners.append(NeMoScanner())
            logger.info("G1 security: NeMoScanner appended to GuardrailsEngine chain")
        return ctx

    # 底座未包装（security.enabled 但 secret/pii scanner 全关）：Ultima fail-closed 包装
    try:
        mode = RedactionMode(getattr(config.security, "mode", "block"))
    except Exception:
        mode = RedactionMode.BLOCK
    ctx.engine = GuardrailsEngine(
        engine,
        scanners=[NeMoScanner()],
        mode=mode,
        scan_input=getattr(config.security, "scan_input", True),
        scan_output=getattr(config.security, "scan_output", True),
        bus=bus,
    )
    logger.info("G1 security: GuardrailsEngine(NeMoScanner) wrapped (fail-closed)")
    return ctx


def _patch_setup_security() -> bool:
    """把 openjarvis.security.setup_security 替换为 Ultima 包装版。

    ask.py 在函数体内 ``from openjarvis.security import setup_security``，
    调用时取模块最新属性，因此替换模块属性即可被真实消费。
    """
    global _ORIGINAL_SETUP_SECURITY
    import openjarvis.security as _sec_mod

    if getattr(_sec_mod, "_ultima_bootstrap_patched", False):
        logger.info("G1 security: setup_security already patched, skip")
        return True

    # 先缓存底座原函数引用，再替换模块属性——包装版内部必须调用原版，
    # 不能 from-import（会取到替换后的自己，导致无限递归）
    _ORIGINAL_SETUP_SECURITY = _sec_mod.setup_security
    _sec_mod.setup_security = _ultima_setup_security
    _sec_mod._ultima_bootstrap_patched = True
    logger.info("G1 security: openjarvis.security.setup_security patched")
    return getattr(_sec_mod, "_ultima_bootstrap_patched", False)


# ---------------------------------------------------------------------------
# G4 · L2 技能白名单：任务域 11 技能静态登记（P2 #62）
# ---------------------------------------------------------------------------
def _install_skill_whitelist() -> bool:
    """登记任务域 11 技能至 SkillRegistry（幂等，驻留）。

    对齐 registry.md「先静态登记、后运行时注册」与 plugin-bus-spec
    试点插件 ultima.domain.skill 的静态登记前置。
    """
    try:
        from src.brain.skills.registry import SkillRegistry

        count = SkillRegistry.install_task_domain()
        logger.info("G4 skills: task-domain skills registered (+%d)", count)
        return SkillRegistry.exists("eng.code")
    except Exception as exc:  # pragma: no cover - 登记失败不阻断底座主链
        logger.warning("G4 skills: task-domain registration failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# G5 · L9 偏好最小记忆：PreferenceStore 语义层（P2 #63）
# ---------------------------------------------------------------------------
_PREFERENCE_STORE: Any = None


def get_preference_store() -> Any:
    """返回全局偏好语义层实例（install 后可用；未 install 时惰性构建）。"""
    if _PREFERENCE_STORE is None:
        _install_preference_store()
    return _PREFERENCE_STORE


def _install_preference_store() -> bool:
    """实例化 PreferenceStore 并持有全局引用（幂等）。"""
    global _PREFERENCE_STORE
    if _PREFERENCE_STORE is not None:
        return True
    try:
        from src.brain.memory.preference import PreferenceStore

        _PREFERENCE_STORE = PreferenceStore()
        logger.info(
            "G5 preference: PreferenceStore ready (%s)",
            _PREFERENCE_STORE.snapshot()["data_dir"],
        )
        return True
    except Exception as exc:  # pragma: no cover - 失败不阻断底座主链
        logger.warning("G5 preference: PreferenceStore init failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# G6 · L0/L6 悬浮球状态机（P2 #64，Claw 路线 + emotionId）
# ---------------------------------------------------------------------------
_ORB_STATE_MACHINE: Any = None


def get_orb_state_machine() -> Any:
    """返回全局悬浮球状态机（install 后可用；未 install 时惰性构建）。"""
    if _ORB_STATE_MACHINE is None:
        _install_orb_state_machine()
    return _ORB_STATE_MACHINE


def _install_orb_state_machine() -> bool:
    """实例化 OrbStateMachine 并持有全局引用（幂等）。"""
    global _ORB_STATE_MACHINE
    if _ORB_STATE_MACHINE is not None:
        return True
    try:
        from src.brain.display.orb import OrbStateMachine

        _ORB_STATE_MACHINE = OrbStateMachine()
        logger.info("G6 orb: OrbStateMachine ready (idle)")
        return True
    except Exception as exc:  # pragma: no cover - 失败不阻断底座主链
        logger.warning("G6 orb: OrbStateMachine init failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# 配置注入（可选）：避免修改 C 盘全局 config.toml
# ---------------------------------------------------------------------------
def _inject_config(config_path: str) -> bool:
    """Ultima 独立配置文件 → 包装 ask 的 load_config。

    用 OPENJARVIS_CONFIG 语义：把 Ultima 配置文件路径注入环境变量，
    使 ask.py 模块级导入的 load_config() 读取 Ultima 配置而非 C 盘全局
    config.toml。同时补丁 ask 模块内的 load_config 绑定，覆盖
    memory.default_backend / security.mode 等运行时所需键。
    """
    import os

    from pathlib import Path

    p = Path(config_path).expanduser().resolve()
    if not p.exists():
        logger.error("G-config: config file not found: %s", p)
        return False
    os.environ["OPENJARVIS_CONFIG"] = str(p)

    # 兜底：即使环境变量未生效，也显式覆盖 ask 模块绑定的 load_config
    try:
        import openjarvis.cli.ask as _ask_mod

        _orig_load = getattr(_ask_mod, "load_config", None)

        def _ultima_load_config(path: Optional[str] = None):
            from openjarvis.core.config import load_config as _base_load

            cfg = _base_load(path)
            cfg.memory.default_backend = MEMORY_BACKEND_KEY
            cfg.tools.storage.default_backend = MEMORY_BACKEND_KEY
            cfg.security.enabled = True
            if not cfg.security.mode or cfg.security.mode == "redact":
                cfg.security.mode = "block"
            # 执行参数基线（AD-01/02/03，execution-param-contract v0.1）：
            # 底座默认 max_turns=10/temperature=0.7/max_tokens=1024 → 契约基线
            try:
                if getattr(cfg, "agent", None) is not None:
                    cfg.agent.max_turns = 5
            except Exception:
                pass
            try:
                if getattr(cfg, "intelligence", None) is not None:
                    cfg.intelligence.temperature = 0.3
                    cfg.intelligence.max_tokens = 8192
            except Exception:
                pass
            return cfg

        _ask_mod.load_config = _ultima_load_config
        if _orig_load is not None:
            logger.info("G-config: ask.load_config wrapped with Ultima overrides")
        return True
    except Exception as exc:  # pragma: no cover - ask 不可导入时环境变量已足够
        logger.warning("G-config: ask.load_config wrap failed (env fallback): %s", exc)
        return bool(os.environ.get("OPENJARVIS_CONFIG"))


# ---------------------------------------------------------------------------
# 入口（可选：python -m src.brain.bootstrap install）
# ---------------------------------------------------------------------------
if __name__ == "__main__":  # pragma: no cover - CLI 辅助入口
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg_arg = None
    if len(sys.argv) > 1 and sys.argv[1] == "install":
        if len(sys.argv) > 2:
            cfg_arg = sys.argv[2]
        ok = install(config_path=cfg_arg)
        sys.exit(0 if ok else 1)
    print("usage: python -m src.brain.bootstrap install [ultima-config.toml]")
    sys.exit(2)
