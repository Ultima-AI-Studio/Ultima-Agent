"""Validate executable card metadata and stage-level dispatch prerequisites."""
import hashlib
import json
import re
import subprocess
from pathlib import Path


def section(text, name):
    match = re.search(r'^## ' + re.escape(name) + r'[^\n]*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1).strip() if match else ''


def validate_card(task, root, *, runtime=False):
    card = Path(task['card_path'])
    card = card if card.is_absolute() else root / card
    text = card.read_text(encoding='utf-8-sig')
    match = re.search(r'\*\*task_id\*\*\s*[：:]\s*(\S+)', text)
    if not match or match.group(1) != task['task_id']:
        raise ValueError('任务卡 task_id 与索引不一致')
    required = ['goal', 'acceptance[]', 'dependsOn[]', 'fileDomain[]', 'priority',
                'reasoningEffort', 'category + skill', 'receipt', 'retryCount']
    if 'M1' not in text or any(not section(text, key) for key in required):
        raise ValueError('任务卡必填章节或 M1 声明不完整')
    dependencies = []
    for line in section(text, 'dependsOn[]').splitlines():
        if not line.startswith('- '):
            continue
        raw = re.split('[（(]', line[2:])[0].strip().strip('`')
        if raw in {'', '无', '无依赖', 'none', '[]'}:
            continue
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._~-]*', raw):
            raise ValueError('任务卡依赖必须为原始 task_id')
        dependencies.append(raw)
    domains = re.findall(r'`([^`]+)`', section(text, 'fileDomain[]'))
    normalize = lambda values: {str(Path(value).resolve()).casefold() for value in values}
    if set(dependencies) != set(task['dependsOn']) or normalize(domains) != normalize(task['fileDomain']):
        raise ValueError('索引依赖或 fileDomain 与任务卡不一致')
    priority = re.search(r'^-\s*(\d+)\b', section(text, 'priority'), re.M)
    effort = re.search(r'^-\s*(\w+)\b', section(text, 'reasoningEffort'), re.M)
    priority_ok = (type(task['priority']) is int and 0 <= task['priority'] <= 100
                   and (runtime or (priority and int(priority.group(1)) == task['priority'])))
    if not priority_ok or not priority or not effort or effort.group(1) != task['reasoningEffort']:
        raise ValueError('索引优先级或推理强度与任务卡不一致')
    if 'ACCEPT:' not in section(text, 'acceptance[]'):
        raise ValueError('任务卡缺少封闭验收项')
    return card, text


def check_version_gates(task, root):
    card = Path(task['card_path'])
    card = card if card.is_absolute() else root / card
    if not card.is_file():
        # Low-level engine callers can use synthetic tasks; operational CLI validates cards first.
        return
    text = card.read_text(encoding='utf-8-sig')
    stage = re.search(r'^-\s*\*\*stage\*\*[^\n]*\b(v\d+\.\d+)', text, re.M)
    if not stage:
        raise ValueError('任务卡缺少可核对的版本归属')
    version = stage.group(1)
    requirements = {'v0.1': [], 'v0.2': ['v0.1'], 'v0.3': ['v0.1'],
                    'v0.4': ['v0.3'], 'v1.0': ['v0.2', 'v0.4']}
    if version not in requirements:
        raise ValueError('未知阶段版本，拒绝推测冻结门')
    project = root.parent
    for prerequisite in requirements[version]:
        tag = prerequisite + '-frozen'
        receipt = root / 'queue/gates' / (tag + '.json')
        if not receipt.is_file():
            raise ValueError(f'等待工单版本冻结门：{tag}')
        approval = json.loads(receipt.read_text(encoding='utf-8-sig'))
        if not isinstance(approval, dict) or approval.get('gate') != tag or approval.get('decision') != 'PASS' or approval.get('approved_by') != 'owner' or not approval.get('approved_at'):
            raise ValueError(f'版本冻结审批无效：{tag}')
        evidence = approval.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f'版本冻结缺验收证据：{tag}')
        for item in evidence:
            if not isinstance(item, dict):
                raise ValueError('冻结证据格式错误')
            path = Path(item['path'])
            path = path if path.is_absolute() else project / path
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item.get('sha256'):
                raise ValueError(f'版本冻结证据缺失或哈希变化：{tag}')
        result = subprocess.run(['git', '-C', str(project), 'rev-parse', '--verify', 'refs/tags/' + tag],
                                capture_output=True, timeout=10,
                                creationflags=0x08000000 if __import__('os').name == 'nt' else 0)
        if result.returncode:
            raise ValueError(f'版本冻结 tag 不存在：{tag}')
