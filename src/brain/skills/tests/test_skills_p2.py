"""L2 技能白名单注册（P2 #62）测试。

覆盖：
1. 任务域 11 技能静态登记（幂等、六字段齐全、驻留）
2. 白名单策略：未登记拒绝 / 已登记放行 / 动态授权集
3. 任务域派发：精确命中 / generic 兜底 / 未知类型拒绝
4. 驻留管控：驻留技能拒绝热卸载
5. 未授权拒绝 100%（对齐 L8 基线）

运行：<venv-py> -X utf8 -W ignore -m unittest discover -s src\\brain\\tests -p "test_*.py"
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.skills.dispatch import dispatch_decision, resolve_skill
from src.brain.skills.registry import (
    ResidencyViolationError,
    SkillRegistry,
)
from src.brain.skills.whitelist import SkillWhitelist


class TestSkillRegistry(unittest.TestCase):
    def setUp(self):
        SkillRegistry.reset()
        SkillRegistry.install_task_domain()

    def test_task_domain_11_skills_registered(self):
        skills = {r.skill_id for r in SkillRegistry.all()}
        self.assertEqual(
            skills,
            {
                "eng.code", "eng.ui", "eng.audit", "eng.security",
                "eng.arch", "eng.database", "eng.test", "eng.infra",
                "eng.voice", "eng.docs", "eng.generic",
            },
        )

    def test_install_idempotent(self):
        first = SkillRegistry.install_task_domain()
        self.assertEqual(first, 0)  # 已登记，本次新增 0

    def test_record_six_fields(self):
        rec = SkillRegistry.get("eng.code")
        self.assertTrue(rec.role)
        self.assertTrue(rec.scope)
        self.assertEqual(rec.task_types, ("code",))
        self.assertTrue(rec.output_std)
        self.assertTrue(rec.acceptance)

    def test_resident_skills_refuse_unload(self):
        with self.assertRaises(ResidencyViolationError):
            SkillRegistry.unload("eng.code")
        # 非驻留路径仍可卸载（先注册一个非驻留技能）
        SkillRegistry.register(
            "eng.trial",
            role="试点",
            scope="试点技能",
            task_types=("trial",),
            output_std="x",
            acceptance="y",
            resident=False,
        )
        self.assertTrue(SkillRegistry.unload("eng.trial"))

    def test_duplicate_register_rejected(self):
        from src.brain.skills.registry import SkillRegistrationError

        with self.assertRaises(SkillRegistrationError):
            SkillRegistry.register(
                "eng.code",
                role="重复",
                scope="重复登记",
                task_types=("code",),
                output_std="x",
                acceptance="y",
            )


class TestSkillWhitelist(unittest.TestCase):
    def setUp(self):
        SkillRegistry.reset()
        SkillRegistry.install_task_domain()

    def test_registered_skill_allowed(self):
        wl = SkillWhitelist()
        dec = wl.check("eng.code")
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.action, "allow")

    def test_unregistered_skill_denied(self):
        wl = SkillWhitelist()
        dec = wl.check("eng.hacker")
        self.assertFalse(dec.allowed)
        self.assertEqual(dec.action, "deny")
        self.assertIn("未静态登记", dec.reason)

    def test_extra_allowed_skill(self):
        SkillRegistry.register(
            "eng.extra", role="扩展", scope="动态授权试点",
            task_types=("extra",), output_std="x", acceptance="y",
            resident=False,
        )
        wl = SkillWhitelist()
        self.assertFalse(wl.check("eng.extra").allowed)  # 未在授权集
        wl.add("eng.extra")
        self.assertTrue(wl.check("eng.extra").allowed)   # 授权后放行
        wl.remove("eng.extra")
        self.assertFalse(wl.check("eng.extra").allowed)

    def test_unregistered_denied_even_extra(self):
        # require_registered=True 时，未登记技能即使进授权集也拒绝
        wl = SkillWhitelist(allowed_skills={"eng.ghost"})
        dec = wl.check("eng.ghost")
        self.assertFalse(dec.allowed)


class TestTaskDomainDispatch(unittest.TestCase):
    def setUp(self):
        SkillRegistry.reset()
        SkillRegistry.install_task_domain()

    def test_exact_hit(self):
        dec = dispatch_decision("code")
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.skill_id, "eng.code")

    def test_voice_hit(self):
        self.assertEqual(resolve_skill("voice"), "eng.voice")

    def test_generic_fallback(self):
        dec = dispatch_decision("unknown-category")
        self.assertTrue(dec.allowed)
        self.assertEqual(dec.skill_id, "eng.generic")
        self.assertIn("兜底", dec.reason)

    def test_no_fallback_when_disabled(self):
        dec = dispatch_decision("unknown-category", fallback_generic=False)
        self.assertFalse(dec.allowed)
        self.assertIn("无法命中", dec.reason)

    def test_dispatch_via_whitelist_denied(self):
        # 白名单置空授权集（require_registered=False 时全拒）
        wl = SkillWhitelist(require_registered=False)
        dec = dispatch_decision("code", wl)
        self.assertFalse(dec.allowed)


if __name__ == "__main__":
    unittest.main()
