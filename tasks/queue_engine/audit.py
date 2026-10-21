"""Receipt audit, fail-closed closeout, and run recovery."""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .state_machine import QueueState, StateMachine
from .storage import QueueStorage, queue_transaction


SUMMARY_REQUIRED_FIELDS = frozenset(
    {
        "version",
        "work_order",
        "task_id",
        "business_success",
        "exit_code",
        "receipt_present",
        "developer_skill",
        "auditor_skill",
        "file_domain_ok",
        "registry_entry",
        "developer_id", "auditor_id",
    }
)
RECEIPT_REQUIRED_FIELDS = frozenset(
    {"completion", "landed_files", "reviewReason", "stdoutText", "evidence", "acceptance"}
)
VERSION_PATTERN = re.compile(r"^S1/v0\.\d+$")


@dataclass(frozen=True)
class AuditResult:
    verdict: str
    reasons: tuple[str, ...]
    correction_task: dict[str, Any] | None = None


class AuditEngine:
    def __init__(self, storage: QueueStorage, report_root: str | Path, registry_path: str | Path, *, auditor_id: str | None = None) -> None:
        self.storage = storage
        self.report_root = Path(report_root).resolve()
        self.registry_path = Path(registry_path).resolve()
        self.machine = StateMachine(storage)
        self._approvals: dict[str, tuple[AuditResult, dict[str, str], str, str]] = {}
        # A trusted caller supplies the authenticated reviewer principal. This
        # local library deliberately does not authenticate agents from labels.
        self.auditor_id = auditor_id

    def audit(
        self,
        task: dict[str, Any],
        receipt: dict[str, Any] | None,
        summary: dict[str, Any],
        *,
        auditor_skill: str,
    ) -> AuditResult:
        unclear: list[str] = []
        defects: list[str] = []
        self._approvals.pop(task.get('task_id'), None)

        missing_summary = sorted(SUMMARY_REQUIRED_FIELDS - set(summary))
        if missing_summary:
            unclear.append(f"执行报告缺字段：{', '.join(missing_summary)}")
        version = summary.get("version")
        if not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
            unclear.append("执行报告 version 必须符合 S1/v0.x")
        if summary.get("task_id") != task.get("task_id"):
            unclear.append("执行报告 task_id 与任务不一致")

        if receipt is None:
            unclear.append("缺少任务回执")
        else:
            missing_receipt = sorted(RECEIPT_REQUIRED_FIELDS - set(receipt))
            if missing_receipt:
                unclear.append(f"回执缺字段：{', '.join(missing_receipt)}")
            for key in ("completion", "reviewReason", "stdoutText"):
                if not isinstance(receipt.get(key), str) or not receipt[key].strip():
                    unclear.append(f"回执 {key} 为空")
            if not isinstance(receipt.get("landed_files"), list) or not receipt["landed_files"]:
                unclear.append("回执缺落地文件清单")
            if not isinstance(receipt.get("evidence"), list) or not receipt["evidence"]:
                unclear.append("回执缺验收证据")
            acceptance = receipt.get("acceptance")
            if not isinstance(acceptance, dict) or not acceptance or not all(
                value is True for value in acceptance.values()
            ):
                unclear.append("回执 acceptance 未逐项全绿")

        developer_skill = summary.get("developer_skill")
        if auditor_skill != "eng.audit" or developer_skill == auditor_skill:
            unclear.append("开发与审计技能未分离")
        if summary.get("auditor_skill") != auditor_skill:
            unclear.append("执行报告审计技能与实际审计者不一致")
        developer_id = summary.get('developer_id')
        if not isinstance(developer_id, str) or not developer_id.strip() or not self.auditor_id or summary.get('auditor_id') != self.auditor_id or developer_id == self.auditor_id:
            unclear.append('真实开发与审计身份未分离或审计调用方身份未核验')
        card = Path(task['card_path'])
        card = card if card.is_absolute() else self.storage.root / card
        try:
            from .card_contract import section
            checks = re.findall(r'^-\s*(?:\[[ xX]\]\s*)?ACCEPT:\s*(.+)$', section(card.read_text(encoding='utf-8-sig'), 'acceptance[]'), re.M)
            if not checks or receipt is None or set(receipt.get('acceptance', {})) != set(checks):
                unclear.append('回执 acceptance 未与任务卡封闭验收项逐项绑定')
            orders = [path for path in self.storage.queue_dir.glob('wo-*.md')
                      if re.search(r'(?<![A-Za-z0-9_-])' + re.escape(task['task_id'].split('~r')[0]) + r'(?![A-Za-z0-9_-])', path.read_text(encoding='utf-8-sig'))]
            if len(orders) != 1 or orders[0].stem != summary.get('work_order'):
                unclear.append('执行报告 work_order 与任务所属工单不一致或所属关系不唯一')
        except (OSError, ValueError, TypeError):
            unclear.append('任务卡封闭验收清单或所属工单不可验证')

        landed_files = receipt.get("landed_files", []) if receipt else []
        file_domain_ok = self._all_paths_in_domain(landed_files, task.get("fileDomain", []))
        if not file_domain_ok or summary.get("file_domain_ok") is not True:
            defects.append("产物路径超出 fileDomain 或报告未确认路径核对")
        registry_entry = summary.get("registry_entry")
        if not self._registry_contains(registry_entry):
            defects.append("组件注册表核对失败")

        if summary.get("receipt_present") is not True:
            unclear.append("执行报告未确认回执存在")
        if summary.get("exit_code") != 0:
            defects.append(f"进程退出码非 0：{summary.get('exit_code')!r}")
        if summary.get("business_success") is not True:
            defects.append("业务结果未成功；退出码 0 不能替代业务通过")

        if unclear:
            return AuditResult("BLOCKED", tuple(dict.fromkeys(unclear)))
        if defects:
            correction = {
                "task_id": f"{task['task_id']}~r1",
                "goal": "修复审计发现的问题",
                "reasons": defects,
            }
            return AuditResult("REVISE", tuple(dict.fromkeys(defects)), correction)
        try:
            proof: dict[str, str] = {}
            for raw in [*landed_files, *receipt['evidence']]:
                path = Path(raw).resolve()
                if not path.is_file():
                    raise ValueError(f'产物或证据不存在：{path}')
                proof[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            task_id = task['task_id']
            done_paths = sorted((self.storage.runs_dir/task_id).glob(f'{task_id}.*.done'),reverse=True)
            if not done_paths:
                raise ValueError('审计缺少对应真实 run')
            run = done_paths[0]
            captured = {str(run.with_suffix(s)):run.with_suffix(s).read_bytes() for s in ('.done','.out','.before')}
            done=json.loads(captured[str(run)])
            before=json.loads(captured[str(run.with_suffix('.before'))])
            business=json.loads(captured[str(run.with_suffix('.out'))].splitlines()[-1])
            if done.get('exit_code')!=0 or before.get('task_id')!=task_id or before.get('developer_id') != developer_id or business.get('business_success') is not True:
                raise ValueError('真实 run 与任务或成功声明不一致')
            proof.update({name:hashlib.sha256(data).hexdigest() for name,data in captured.items()})
            proof[str(card.resolve())] = hashlib.sha256(card.read_bytes()).hexdigest()
            proof[str(orders[0].resolve())] = hashlib.sha256(orders[0].read_bytes()).hexdigest()
        except (OSError,ValueError,TypeError,IndexError,AttributeError) as exc:
            return AuditResult('BLOCKED',(f'真实文件或运行证据验证失败：{exc}',))
        result=AuditResult("PASS", ("回执、真实文件、运行证据、角色、路径与业务结果全部核实通过",))
        self._approvals[task_id]=(result,proof,json.dumps(task,sort_keys=True),str(run))
        return result

    @queue_transaction
    def close(self, task_id: str, result: AuditResult) -> dict[str, Any]:
        tasks = self.storage.load_tasks()
        task = next((item for item in tasks if item["task_id"] == task_id), None)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if result.verdict == "PASS":
            approved=self._approvals.get(task_id)
            if approved is None or approved[0] is not result:
                raise ValueError('PASS 未由本次真实审计生成，须重新审计')
            latest=sorted((self.storage.runs_dir/task_id).glob(f'{task_id}.*.done'),reverse=True)
            if json.dumps(task,sort_keys=True)!=approved[2] or not latest or str(latest[0])!=approved[3]:
                raise ValueError('任务版本或运行轮次已变化，旧 PASS 不得关闭新一轮任务')
            for name,digest in approved[1].items():
                if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:
                    raise ValueError('审计后证据已变化，须重新审计')
            updated, _ = self.machine.transition(
                task,
                QueueState.COMPLETED,
                actor="auditor",
                reason="独立审计证据明确通过",
                audit_passed=True,
            )
        elif result.verdict == "REVISE":
            updated, _ = self.machine.transition(
                task,
                QueueState.FAILED,
                actor="auditor",
                reason="；".join(result.reasons),
            )
        else:
            updated, _ = self.machine.block_for_unclear_audit(
                task,
                actor="auditor",
                reason="；".join(result.reasons),
            )
        self.storage.save_tasks(updated if item is task else item for item in tasks)
        self._approvals.pop(task_id,None)
        return updated

    def write_summary(self, task_id: str, summary: dict[str, Any]) -> Path:
        task_report_dir = self.report_root / task_id
        task_report_dir.mkdir(parents=True, exist_ok=True)
        path = task_report_dir / "summary.json"
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _all_paths_in_domain(paths: list[Any], domains: list[Any]) -> bool:
        try:
            resolved_domains = [Path(domain).resolve() for domain in domains]
            for raw_path in paths:
                path = Path(raw_path).resolve()
                if not any(path == domain or path.is_relative_to(domain) for domain in resolved_domains):
                    return False
        except (OSError, TypeError, ValueError):
            return False
        return bool(paths and resolved_domains)

    def _registry_contains(self, entry: Any) -> bool:
        if not isinstance(entry, str) or not entry:
            return False
        try:
            return f"`{entry}`" in self.registry_path.read_text(encoding="utf-8")
        except OSError:
            return False


class RecoveryManager:
    def __init__(self, storage: QueueStorage) -> None:
        self.storage = storage
        self.machine = StateMachine(storage)

    @queue_transaction
    def create_correction(self, task_id: str, *, actor: str, reason: str) -> dict[str, Any]:
        """Queue an explicit repair child; original validation waits for its audit.

        The original ID stays stable for downstream dependencies. It retries only
        after the correction child is independently COMPLETED, never on exit 0.
        """
        if actor not in {'human', 'brain'} or not reason.strip():
            raise ValueError('修正任务只能由人工/主脑明确发起并说明原因')
        tasks = self.storage.load_tasks()
        original = next((task for task in tasks if task['task_id'] == task_id), None)
        if original is None or original['state'] not in {'FAILED', 'BLOCKED'}:
            raise ValueError('仅失败或冻结的任务可建立修正链')
        if original['state'] == 'FAILED' and self.machine._retry_count(original) >= 2:
            updated, _ = self.machine.retry_or_block(original, actor=actor, reason='两次重试已耗尽，禁止自动增加修正')
            self.storage.save_tasks(updated if task is original else task for task in tasks)
            return updated
        root_id = task_id.split('~r')[0]
        sequence = max([0] + [int(task['task_id'].split('~r')[-1]) for task in tasks
                       if re.fullmatch(re.escape(root_id) + r'~r\d+', task['task_id'])]) + 1
        correction_id = f'{root_id}~r{sequence}'
        card = Path(original['card_path'])
        card = card if card.is_absolute() else self.storage.root / card
        body = card.read_text(encoding='utf-8-sig')
        if f'**task_id**：{task_id}' not in body or '## dependsOn[]' not in body:
            raise ValueError('原卡ID或依赖章节缺失，拒绝猜测生成修正卡')
        child_card = self.storage.cards_dir / correction_id / 'task.md'
        if child_card.exists():
            raise ValueError('修正卡已存在，禁止覆盖历史')
        child = dict(original, task_id=correction_id, state='QUEUED',
                     dependsOn=list(original['dependsOn']), terminal_reason=None,
                     card_path=str(child_card), created_at=datetime.now(UTC).isoformat())
        child['updated_at'] = child['created_at']
        child_body = body.replace(f'**task_id**：{task_id}', f'**task_id**：{correction_id}', 1)
        child['fileDomain'] = [str(child_card.parent) if Path(domain).resolve() == card.parent.resolve()
                               else domain for domain in original['fileDomain']]
        child_body = child_body.replace(str(card.parent), str(child_card.parent))
        child_body += f'\n\n## 修正关联\n\n- 原任务：{task_id}\n- 裁决人：{actor}\n- 原因：{reason}\n- 本卡仍按原封闭验收项重新验证，不继承历史通过结论。\n'
        child_body = re.sub(r'- \[[xX]\] ACCEPT:', '- [ ] ACCEPT:', child_body)
        child_body = re.sub(r'(## receipt[^\n]*\n).*?(?=\n## )', r'\1\n- reviewReason: 待独立核验\n- stdoutText: 待填\n- evidence: 待填\n- acceptance: 待逐项核验\n', child_body, flags=re.S)
        parent_body = body.replace('## dependsOn[]', f'## dependsOn[]\n\n- {correction_id}（修正任务独立审计完成后，原任务才允许重新验证）', 1)
        updated, event = self.machine.transition(original, QueueState.QUEUED, actor=actor, reason=f'修正 {correction_id}：{reason}')
        updated['dependsOn'] = list(original['dependsOn']) + [correction_id]
        candidate = [updated if task is original else task for task in tasks] + [child]
        from .priority_deps import QueuePlanner
        QueuePlanner.validate_acyclic(candidate)
        backup = self.storage.archive_dir / f'{correction_id}.parent-before.md'
        with backup.open('x', encoding='utf-8') as stream:
            stream.write(body)
        child_card.parent.mkdir(parents=True)
        child_card.write_text(child_body, encoding='utf-8')
        temporary = card.with_suffix('.correction.tmp')
        temporary.write_text(parent_body, encoding='utf-8')
        temporary.replace(card)
        self.storage.append_event(correction_id, {**event, 'from': None, 'to': 'QUEUED',
                                                   'parent_task_id': task_id, 'reason': reason})
        self.storage.save_tasks(candidate)
        return child

    @queue_transaction
    def recover_finished_run(self, task_id: str) -> tuple[dict[str, Any], str]:
        tasks = self.storage.load_tasks()
        task = next((item for item in tasks if item["task_id"] == task_id), None)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["state"] != QueueState.EXECUTING.value:
            return task, "任务不在执行中，恢复不重复推进"

        from .dispatcher import Dispatcher
        try:
            if Dispatcher(self.storage)._session_running(task_id):
                return task, "真实执行进程仍在运行，不修改状态"
        except (OSError, ValueError):
            return task, "执行进程身份未能确认，保留原状态并停止恢复"

        done_files = sorted((self.storage.runs_dir / task_id).glob(f"{task_id}.*.done"), reverse=True)
        if not done_files or done_files[0].stat().st_size == 0:
            # A detached worker can outlive its supervisor. Keep its WIP slot until
            # termination is established; missing receipt is not proof of exit.
            return task, '缺少完成回执且无法确认全部执行进程终止，保留 EXECUTING 等主脑核查'
        else:
            try:
                done = json.loads(done_files[0].read_text(encoding="utf-8"))
                if not isinstance(done, dict) or type(done.get('exit_code')) is not int:
                    raise ValueError('done 必须是包含整数 exit_code 的对象')
            except (OSError, ValueError) as exc:
                updated, _ = self.machine.block_for_unclear_audit(
                    task, actor="auditor", reason=f"done 证据不可读：{type(exc).__name__}"
                )
                message = "done 证据不可读，恢复判冻结"
            else:
                if done.get("exit_code") == 0:
                    updated, _ = self.machine.transition(
                        task,
                        QueueState.SELF_CHECK,
                        actor="recovery",
                        reason="已有进程完成证据，恢复到自检而非重复执行",
                    )
                    message = "恢复到自检，未重复执行"
                else:
                    updated, _ = self.machine.transition(
                        task,
                        QueueState.FAILED,
                        actor="recovery",
                        reason=f"进程退出码 {done.get('exit_code')!r}",
                    )
                    message = "进程失败，恢复到失败"
        self.storage.save_tasks(updated if item is task else item for item in tasks)
        return updated, message

    @queue_transaction
    def finish_self_check(self, task_id: str, *, passed: bool, evidence: str) -> dict[str, Any]:
        tasks = self.storage.load_tasks()
        task = next((item for item in tasks if item["task_id"] == task_id), None)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        target = QueueState.AUDIT if passed else QueueState.FAILED
        updated, _ = self.machine.transition(
            task,
            target,
            actor="self-check",
            reason=evidence,
        )
        self.storage.save_tasks(updated if item is task else item for item in tasks)
        return updated

    @queue_transaction
    def finish_self_check_from_run(self, task_id: str) -> dict[str, Any]:
        """Use the run's structured business result; exit code alone never passes."""
        tasks = self.storage.load_tasks()
        task = next((item for item in tasks if item["task_id"] == task_id), None)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        if task["state"] != QueueState.SELF_CHECK.value:
            raise ValueError(f"task is not in SELF-CHECK: {task['state']}")
        done_files = sorted((self.storage.runs_dir / task_id).glob(f"{task_id}.*.done"), reverse=True)
        if not done_files:
            updated, _ = self.machine.block_for_unclear_audit(
                task, actor="auditor", reason="自检缺少 done 文件"
            )
        else:
            out_path = done_files[0].with_suffix(".out")
            try:
                lines = [line for line in out_path.read_text(encoding="utf-8").splitlines() if line.strip()]
                business = json.loads(lines[-1])
            except (OSError, UnicodeError, IndexError, json.JSONDecodeError) as exc:
                updated, _ = self.machine.block_for_unclear_audit(
                    task, actor="auditor", reason=f"业务结果证据不可读：{type(exc).__name__}"
                )
            else:
                passed = isinstance(business, dict) and business.get("business_success") is True
                target = QueueState.AUDIT if passed else QueueState.FAILED
                reason = "结构化业务结果明确成功" if passed else "结构化业务结果明确失败"
                updated, _ = self.machine.transition(
                    task, target, actor="self-check", reason=reason
                )
        self.storage.save_tasks(updated if item is task else item for item in tasks)
        return updated

    @queue_transaction
    def block_nonterminal_closeout(self) -> list[str]:
        tasks = self.storage.load_tasks()
        changed: list[str] = []
        for index, task in enumerate(tasks):
            if task["state"] in {QueueState.COMPLETED.value, QueueState.CANCELLED.value}:
                continue
            if task['state'] == QueueState.EXECUTING.value:
                # Audit closeout must not release the WIP slot of a live or
                # unconfirmed detached worker; use finished-run recovery first.
                continue
            updated, _ = self.machine.block_for_unclear_audit(
                task, actor="auditor", reason="审计收尾发现悬空非终态"
            )
            tasks[index] = updated
            changed.append(task["task_id"])
        if changed:
            self.storage.save_tasks(tasks)
        return changed
