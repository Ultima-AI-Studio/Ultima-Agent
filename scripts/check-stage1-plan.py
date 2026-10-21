"""Validate task IDs/dependencies directly from the current 25 task cards."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.card_contract import validate_card


def section(text, name):
    match = re.search(r'^## ' + re.escape(name) + r'\s*\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1) if match else ''


def inspect():
    cards = {}
    problems = []
    for path in sorted((ROOT / 'tasks/cards').glob('s1-*/task.md')):
        text = path.read_text(encoding='utf-8-sig')
        task_id = path.parent.name
        deps = []
        for line in section(text, 'dependsOn[]').splitlines():
            if not line.startswith('- '):
                continue
            value = line[2:].split('（')[0].split('(')[0].strip().strip('`')
            if value in {'无', '无依赖', 'none', '[]'} or not value:
                continue
            if not re.fullmatch(r's1-[a-z0-9-]+', value):
                problems.append(f'{task_id}: 非法依赖 ID: {value}')
            else:
                deps.append(value)
        cards[task_id] = deps
        try:
            priority = re.search(r'^-\s*(\d+)\b', section(text, 'priority'), re.M)
            effort = re.search(r'^-\s*(\w+)\b', section(text, 'reasoningEffort'), re.M)
            if not priority or not effort or not re.search(r'^-\s*\*\*stage\*\*[^\n]*\b(v\d+\.\d+)', text, re.M):
                raise ValueError('版本、优先级或推理强度缺失')
            validate_card(dict(task_id=task_id, card_path=str(path), dependsOn=deps,
                               fileDomain=re.findall(r'`([^`]+)`', section(text, 'fileDomain[]')),
                               priority=int(priority.group(1)), reasoningEffort=effort.group(1)), ROOT / 'tasks')
        except (ValueError, OSError) as exc:
            problems.append(f'{task_id}: {exc}')
    for task_id, deps in cards.items():
        for dep in deps:
            if dep not in cards:
                problems.append(f'{task_id}: 依赖任务不存在: {dep}')
    visiting, visited = [], set()

    def visit(task_id):
        if task_id in visiting:
            problems.append('依赖环: ' + ' -> '.join(visiting + [task_id]))
            return
        if task_id in visited:
            return
        visiting.append(task_id)
        for dep in cards.get(task_id, []):
            visit(dep)
        visiting.pop()
        visited.add(task_id)

    for task_id in cards:
        visit(task_id)
    if len(cards) != 25:
        problems.append(f'任务卡数量应为25，实际{len(cards)}')
    print(json.dumps({'cards': len(cards), 'problems': problems}, ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(inspect())
