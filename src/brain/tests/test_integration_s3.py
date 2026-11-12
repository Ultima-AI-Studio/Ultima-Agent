"""整链路联调：S3 批次模块端到端连通性测试（M05~M27 域链路）。

场景：语音/文字意图入口 → 闸门 → 队列七阶段 → 能力执行（检索/记忆）→ 自检
→ 审计 → 回执；行为映射；心跳让位；渠道审批红线；设备前置链；环境档案。

全部数据落 tempfile 临时目录；外部引擎/浏览器用桩执行层（编排层真实）。
"""

import json
import tempfile
import unittest
from pathlib import Path

from src.brain.environment_upgrade import EnvProfileStore, build_profile, HealthReporter
from src.brain.guardrails import (
    AppendOnlyAuditLog,
    ReceiptValidator,
    ScopePolicy,
)
from src.brain.guardrails.supply_chain import SupplyChainGate
from src.brain.memory import MemoryLayers
from src.brain.orchestration.queue import TaskQueue
from src.brain.voice.fullchain import UnifiedIntentEntry
from src.brain.display.behavior import BehaviorMapper
from src.brain.heartbeat.ticker import HeartbeatConfig, HeartbeatTicker
from src.brain.channel.ime_bridge import ImBridge
from src.brain.iot.device_profile import DeviceRegistry, ProvisionChain
from src.brain.search.upgrade import SearchOrchestrator


def make_tmp(prefix: str = "intg_s3_") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


class TestIntegrationS3(unittest.TestCase):
    """整链路联通：主脑回路（意图→闸门→队列→执行→审计→回执→可视化）。"""

    def test_voice_intent_to_queue_to_receipt(self):
        """语音意图入口 → 任务入队 → 七阶段闭环 → 回执校验。"""
        d = make_tmp()
        audit = AppendOnlyAuditLog(d / "audit.jsonl")
        queue = TaskQueue(d / "queue")
        # 1) 语音/文字同入口（handle 返回 intent/ok/text/ts）
        intent = UnifiedIntentEntry()
        entry = intent.handle("帮我查一下任务状态", channel="voice")
        self.assertTrue(entry["ok"])
        self.assertEqual(entry["intent"], "task_query")
        audit.append("chain.intent", "ultima.voice", {"intent": entry["intent"]})
        # 2) 任务登记→排队
        rec = queue.create("查询任务状态", priority=1, permissions=("read",))
        queue.enqueue(rec.task_id)
        # 3) 七阶段推进
        for phase in ("派发", "执行", "自检", "审计"):
            queue.advance(rec.task_id, phase)
        receipt = {
            "work_order": rec.task_id,
            "status": "COMPLETED",
            "reviewReason": "联调：任务状态查询完成",
            "stdoutText": "ok",
            "evidence": [{"path": "src/brain/tests/test_integration_s3.py", "kind": "test",
                          "summary": "整链路联调用例"}],
            "acceptance": [{"id": "ACCEPT-1", "result": "PASS",
                            "evidence": "整链路联调用例全绿"}],
        }
        queue.complete(rec.task_id, receipt)
        audit.append("chain.receipt", "ultima.orchestration",
                     {"task_id": rec.task_id})
        # 4) 回执独立校验
        tmp_rc = d / "rc.json"
        tmp_rc.write_text(json.dumps(receipt, ensure_ascii=False), encoding="utf-8")
        r2 = ReceiptValidator(base=Path(".")).validate(str(tmp_rc))
        self.assertTrue(r2.ok and not r2.issues)
        # 5) 审计留痕可查询
        self.assertEqual(len(audit.query(event_type="chain.intent")), 1)
        self.assertEqual(len(audit.query(event_type="chain.receipt")), 1)

    def test_guard_gate_blocks_before_queue(self):
        """供应链闸门 + 权限闸门：不合格模块/越权权限在队列外被拒。"""
        d = make_tmp()
        gate = SupplyChainGate(d / "supply.json")
        gate.register("mod-a", "1.0.0", source="github", license="MIT",
                      owner_approved=True, security_reviewed=True)
        r1 = gate.gate_load("mod-a", "1.0.0")
        self.assertTrue(r1["allowed"], r1.get("errors"))
        r2 = gate.gate_load("mod-evil", "9.9.9")
        self.assertFalse(r2["allowed"])
        # ScopePolicy 权限闸门
        sp = ScopePolicy(cap=["read"], dev=[], cred=[], audit_path=str(d / "sp-audit.jsonl"))
        self.assertTrue(sp.check_scope("cap:read").allowed)
        denied = sp.check_scope("cap:shell_exec")
        self.assertFalse(denied.allowed)

    def test_env_profile_persist_and_health(self):
        """环境快照 → 档案持久化 → 基线比对 → 体检汇报（中文结论键）。"""
        d = make_tmp()
        store = EnvProfileStore(d / "profiles")
        profile = build_profile()
        store.save(profile)
        latest = store.load_latest()
        self.assertEqual(latest.captured_at, profile.captured_at)
        diff = store.diff(profile, latest)
        hr = HealthReporter()
        rep = hr.report(profile, diff)
        # 结论先行（异常/正常）+ 异常优先
        self.assertIn(rep["结论"], ("正常", "异常"))
        self.assertIn("异常优先", rep)
        self.assertIn("硬件摘要", rep)

    def test_behavior_mapping_consumes_chain_events(self):
        """行为层消费链路事件（task/voice/queue）→ 三态映射一致。"""
        bm = BehaviorMapper()
        self.assertEqual(bm.map("voice.thinking").state, "thinking")
        self.assertEqual(bm.map("task.done").state, "idle")
        # coverage 是属性（全量注册事件清单）
        cov = bm.coverage
        for ev in ("voice.thinking", "voice.listening", "voice.speaking",
                   "task.running", "task.done", "task.error", "queue.progress"):
            self.assertIn(ev, cov)
        # 未知事件兜底 idle
        self.assertEqual(bm.map("unknown.event").state, "idle")

    def test_channel_approval_and_redline(self):
        """渠道：IM 入站 → 普通动作执行 → 高危两端审批 → 红线拒绝。"""
        d = make_tmp()
        br = ImBridge(d)
        msg = br.inbound("feishu", "u-1", "查任务")
        self.assertEqual(msg.channel, "feishu")
        r = br.act("read_task", "查询")
        self.assertTrue(r["ok"])
        # 高危动作两端审批
        r2 = br.act("send_money", "转账", approval_id="intg-ap1")
        self.assertEqual(r2["status"], "pending")
        br.approve("intg-ap1", "im", True)
        br.approve("intg-ap1", "desktop", True)
        settled = br.settle("intg-ap1")
        self.assertEqual(settled["status"], "approved")
        # 红线：不代登录
        r3 = br.act("ask_password", "x")
        self.assertFalse(r3["ok"])

    def test_device_chain(self):
        """设备前置链：发现→凭证→可控性。"""
        d = make_tmp()
        reg = DeviceRegistry(d)
        chain = ProvisionChain(reg)
        chain.discover("dev-l1", "客厅灯", "matter", entity_type="light")
        chain.provision("dev-l1", "cred://l1")
        ok = chain.check("dev-l1", reachable=True)
        self.assertTrue(ok["ok"])
        self.assertTrue(ok["controlability"]["controllable"])
        # 不可达如实报告
        nok = chain.check("dev-l1", reachable=False)
        self.assertIn("不可达", nok["controlability"]["reason"])

    def test_heartbeat_preempt_in_busy_chain(self):
        """心跳：忙态等待 + 新消息让位（不打断用户）。"""
        state = {"s": "listening"}
        hb = HeartbeatTicker(config=HeartbeatConfig(idle_budget_max=2),
                             busy_state_provider=lambda: state["s"])
        r = hb.tick()
        self.assertEqual(r["action"], "等待")
        state["s"] = "idle"
        hb.preempt.notify()
        r2 = hb.tick()
        self.assertEqual(r2["action"], "让位")

    def test_search_engine_chain_with_ssrf(self):
        """检索：多引擎降级 + SSRF 剔除（编排层真实、引擎桩）。"""
        so = SearchOrchestrator()
        so.register("primary", lambda q: [{"title": "A", "url": "https://example.com/a",
                                           "snippet": "s"}])
        so.register("fallback", lambda q: [{"title": "B", "url": "https://example.com/b",
                                            "snippet": "s"}])
        r = so.search("联调")
        self.assertEqual(r["engine"], "primary")
        self.assertFalse(r["degraded"])
        # SSRF 目标被剔除（blocked_count 保留真实计数）
        so2 = SearchOrchestrator()
        so2.register("p2", lambda q: [{"title": "INNER", "url": "http://169.254.169.254/",
                                       "snippet": "s"}])
        r2 = so2.search("x")
        self.assertEqual(r2["blocked_count"], 1)
        self.assertEqual(len(r2["results"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
