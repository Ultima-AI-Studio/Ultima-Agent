"""Close the independently accepted host order, without approving a version freeze."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=60, creationflags=0x08000000)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    review_dir = ROOT / 'docs/reports/evidence/w1-independent-20261021/round4-post-reboot'
    review = json.loads((review_dir / 'result.json').read_text(encoding='utf-8'))
    for key in ['technical_W1_pass', 'cleanup_gate_pass', 'may_create_internal_tag', 'W2_core_unchanged']:
        assert review[key] is True, key
    for path, expected in review['source_manifest'].items():
        assert digest(Path(path)) == expected, path
    assert not git('diff', '--cached', '--name-only').strip(), 'Unrelated staged changes'
    assert not git('tag', '--list', 'wo-s1-host-shell-done').strip(), 'Do not rewrite an existing tag'
    assert not git('tag', '--list', 'v0.1-frozen').strip(), 'Owner version gate already exists; reevaluate'
    w2 = json.loads((ROOT / 'docs/reports/evidence/w2-20261021/round2/source-manifest.json').read_text(encoding='utf-8'))
    for path, expected in w2.items():
        path = Path(path)
        if path.is_relative_to(ROOT / 'tasks/queue_engine') or path.is_relative_to(ROOT / 'tasks/tests'):
            assert digest(path) == expected
    target = ROOT / 'docs/reports/evidence/w1-post-reboot-closeout-20261021'
    target.mkdir(exist_ok=False)
    sources = list((ROOT / 'logs/maintenance/w1-restart-20261021').glob('*.json'))
    sources.append(ROOT / 'logs/w1-host-resume-20261021T024845Z/after/root-post-reboot-process-state.json')
    for name in ['w1-post-reboot-final-positive-20261021T0400', 'w1-post-reboot-final-negative-20261021T0401']:
        sources.extend(path for path in (ROOT / 'logs' / name).rglob('*') if path.is_file())
    copies = {}
    for source in sources:
        destination = target / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        assert digest(source) == digest(destination)
        copies[str(source.relative_to(ROOT))] = digest(source)
    evidence_ref = 'docs/reports/evidence/w1-post-reboot-closeout-20261021/'
    message = ('\n\n## 2026-10-21 维护重启后独立收口\n\n'
               'Owner授权维护重启已实际完成；原59328创建身份已不存在，原生枚举与直接内核查询交叉确认，系统清理门解除。'
               '正式入口新正向PASS/exit0、缺Runtime负向FAIL/exit1，0警告/0错误、额外窗口0、当前开机后的后台身份保留。'
               '独立第四轮验收允许工单内部收口；最终证据见 `' + evidence_ref + '` 与 `docs/reports/w1-independent-acceptance-20261021.md`。'
               '旧派发exit125/BLOCKED和历次失败保留。内部tag为wo-s1-host-shell-done；v0.1仍待Owner单独审批。\n')
    for card in ['s1-host-shell-envcheck', 's1-host-shell-winui3-init', 's1-host-shell-webview2', 's1-host-shell-floatingball', 's1-host-shell-selfcheck']:
        directory = ROOT / 'tasks/cards' / card
        for name in ['task.md', 'completion.md', 'acceptance-evidence.md']:
            with (directory / name).open('a', encoding='utf-8') as stream:
                stream.write(message)
        with (directory / 'landed-files.md').open('a', encoding='utf-8') as stream:
            stream.write('\n\n## 重启后最终证据\n\n- `' + evidence_ref + '`：维护、正负向、源/产物绑定及清理证据副本。\n- `docs/reports/evidence/w1-independent-20261021/round4-post-reboot/`：独立验收。\n- 本任务产品实现未在本轮变更，旧文件和失败证据保留。\n')
    order = ROOT / 'tasks/queue/wo-s1-host-shell.md'
    order.write_text(order.read_text(encoding='utf-8').replace('- [ ]', '- [x]') + message, encoding='utf-8')
    docs = ROOT / 'docs/README.md'
    text = docs.read_text(encoding='utf-8')
    text = text.replace('版本冻结仍待W1与Owner审批', 'W1/W2已收口，版本冻结待Owner审批')
    text = text.replace('旧PowerShell59328内核残留未解除，整单W1仍阻塞。', '维护重启后旧PowerShell59328已清除，第四轮独立W1通过，内部tag `wo-s1-host-shell-done`建立；版本冻结待Owner审批。')
    text += '\n当前维护后证据登记：`reports/evidence/w1-post-reboot-closeout-20261021/`；冻结审查材料 `reports/v01-freeze-approval-request-20261021.md`（待Owner决定）。\n'
    docs.write_text(text, encoding='utf-8')
    execution = ROOT / 'tasks/queue/EXECUTION.md'
    execution.write_text(execution.read_text(encoding='utf-8').replace('W1仍待最终运行及独立验收。两单完成和Owner实际审批前', 'W1已在维护重启后独立验收并内部收口。Owner实际审批前'), encoding='utf-8')
    units = ROOT / 'tasks/queue/stage1-unit-queue.md'
    with units.open('a', encoding='utf-8') as stream:
        stream.write('\n\n## 2026-10-21 当前验收状态\n\nW2独立35项/62回归通过；W1维护后独立第四轮通过，两个内部工单tag已建立。v0.1-frozen仍待Owner实际批准，未据此启动后续版本工单。证据见docs/reports/w1-independent-acceptance-20261021.md及w2-independent-acceptance-20261021.md。\n')
    freeze = ROOT / 'docs/reports/v01-freeze-approval-request-20261021.md'
    freeze.write_text('''# v0.1 冻结审批材料（待Owner审批，尚未批准）

本次提交范围：阶段一v0.1环境与承载底座，即工单①队列引擎与工单②宿主壳。不包含后续语音/文本/组合窗口/安装更新完成声明。

| 审批依据 | 证据与结论 |
|---|---|
| W2 | 独立35项验收、62项回归、真实卡及修正子任务→父任务闭环；20份核心源码未变；内部tag wo-s1-queue-engine-done |
| W1 | 独立第四轮技术及系统清理门通过，U01-U05覆盖；内部tag wo-s1-host-shell-done |
| 维护重启 | 新旧开机基线已对比，旧59328创建身份消失；直接内核查询与原生枚举一致；Default输入桌面可用 |
| 正式自检 | w1-post-reboot-final-positive-20261021T0400 PASS/exit0；final-negative-20261021T0401缺Runtime按预期FAIL/exit1；额外窗口0、后台身份保留 |
| 产物绑定 | 0warning/0error，源码运行前后一致，实际进程路径、EXE/DLL与独立清单核对一致 |
| 既有功能 | 真实144/96/96DPI、180逻辑尺寸、位置保持/恢复；原生窗口和真实鼠标拖动已有独立证据 |
| 队列状态 | 两单完成状态、项目镜像及统计已按监督验收同步；旧执行失败回执没有改写 |

## 已知运行限制与历史失败

真实工程派发适配器已接入并经独立代码检查；原host工单Codex进程完成文件后卡在update_plan，监督核验后结束，原done仍为exit125/receipt_valid=false/BLOCKED。本次工单完成依据为后续独立验收与监督收口，不把旧运行伪写成成功，也不宣称已证明长期无人值守Codex连续派发。该限制在冻结审查中保留。

审批证据入口：`w1-independent-acceptance-20261021.md`第四轮、`w2-independent-acceptance-20261021.md`第二轮、`evidence/w1-post-reboot-closeout-20261021/`及两个实际内部tag。

请Owner决定是否批准v0.1冻结。只有收到明确批准后，才登记Owner PASS凭据并创建v0.1-frozen；当前不创建这些、不派发依赖冻结门的后续工单、不远端发布。维护重启授权不作为版本冻结授权。
''', encoding='utf-8')
    paths = ['src/host-shell/README.md', 'docs/README.md', 'docs/reports/w1-independent-acceptance-20261021.md',
             'docs/reports/evidence/w1-independent-20261021/round4-post-reboot',
             'docs/reports/v01-freeze-approval-request-20261021.md', 'tasks/queue/wo-s1-host-shell.md',
             'tasks/queue/stage1-unit-queue.md', 'tasks/queue/EXECUTION.md', 'scripts/check-w1-maintenance-boot.py',
             'scripts/check-w1-post-reboot-desktop.py', 'scripts/close-w1-post-reboot.py']
    paths += ['tasks/cards/' + name for name in ['s1-host-shell-envcheck', 's1-host-shell-winui3-init', 's1-host-shell-webview2', 's1-host-shell-floatingball', 's1-host-shell-selfcheck']]
    git('add', '--', *paths)
    git('add', '-f', '--', str(target.relative_to(ROOT)))
    git('commit', '-m', 'Close-W1-after-authorized-reboot-and-independent-acceptance')
    git('tag', '-a', 'wo-s1-host-shell-done', '-m', 'W1 independent functional and cleanup acceptance; Owner version freeze pending')
    commit = git('rev-parse', 'wo-s1-host-shell-done^{}').decode().strip()
    spec = importlib.util.spec_from_file_location('dispatch_closeout', ROOT / 'scripts/dispatch-work-order.py')
    dispatch = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dispatch)
    before = json.loads((ROOT / 'logs/maintenance/w1-restart-20261021/before.json').read_text(encoding='utf-8'))
    with DispatchLock(dispatch.SHARED / '.engineering-dispatch.lock'):
        for marker in before['dispatch_markers']:
            path = Path(marker['path'])
            assert path.is_file() and digest(path) == marker['sha256'], 'Pause changed; do not remove'
            if marker['created_by_this_maintenance']:
                assert json.loads(path.read_text(encoding='utf-8'))['maintenance_token'] == before['maintenance_token']
        dispatch.state('wo-s1-host-shell', 'frozen', '维护重启后W1独立第四轮通过，原59328已清除；内部tag wo-s1-host-shell-done；旧派发失败保留，v0.1待Owner审批', target, expected='blocked')
        index = dispatch.SHARED / 'global-queue-index.md'
        text = index.read_text(encoding='utf-8')
        text, count = re.subn(r'^- 当前：队列引擎W2独立35项/62回归[^\n]*', '- 当前：队列引擎W2与宿主W1已独立验收并完成内部工单tag；维护重启清除旧自检残留，正负向复验通过；v0.1提交Owner审批，后续6单仍等待各自版本门。旧真实派发失败记录保留。', text, count=1, flags=re.M)
        assert count == 1
        index.write_text(text, encoding='utf-8')
        subprocess.run([sys.executable, str(dispatch.SHARED / 'queue-status-gen.py')], check=True, capture_output=True, timeout=20, creationflags=0x08000000)
        subprocess.run([sys.executable, str(ROOT / 'scripts/reconcile-project-state.py'), '--apply'], check=True, capture_output=True, timeout=20, creationflags=0x08000000)
        removed = []
        for marker in before['dispatch_markers']:
            if marker['created_by_this_maintenance']:
                Path(marker['path']).unlink()
                removed.append(marker['path'])
    assert not git('tag', '--list', 'v0.1-frozen').strip()
    receipt = {'at': datetime.now(timezone.utc).isoformat(), 'W1': 'INTERNAL_ORDER_CLOSED', 'W2': 'INTERNAL_ORDER_CLOSED',
               'commit': commit, 'tag': 'wo-s1-host-shell-done', 'removed_owned_pause_markers': removed,
               'owner_version_decision': 'AWAITING_APPROVAL', 'v01_frozen': False, 'copied_evidence': copies}
    (target / 'closeout-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in receipt.items() if key != 'copied_evidence'}, ensure_ascii=False))

if __name__ == '__main__':
    main()
