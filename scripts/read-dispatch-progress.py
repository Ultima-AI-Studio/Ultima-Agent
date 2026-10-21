"""Read an owned run and its durable tool activity; never print reasoning payloads."""
from datetime import datetime
import json
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import process_identity


def main():
    run = Path(sys.argv[1]).resolve()
    if not run.is_relative_to(ROOT / 'tasks/queue/runs'):
        raise ValueError('Run outside this workspace')
    session = json.loads((run / 'session.json').read_text(encoding='utf-8'))
    events = [json.loads(line) for line in (run / 'out.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    thread = next((entry.get('thread_id') for entry in events if entry.get('type') == 'thread.started'), None)
    started = datetime.fromisoformat(session['started_at'])
    month = Path.home() / '.codex/sessions' / str(started.year) / f'{started.month:02d}'
    matches = list(month.glob(f'*/*{thread}.jsonl')) if thread else []
    calls, last_tool, last_message = [], None, None
    if len(matches) == 1:
        for line in matches[0].read_text(encoding='utf-8').splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            payload = entry.get('payload', {})
            if payload.get('type') in {'custom_tool_call', 'function_call', 'mcp_tool_call_end'}:
                invocation = payload.get('invocation', {})
                last_tool = {'at': entry.get('timestamp'), 'tool': payload.get('name') or invocation.get('tool')}
                title = invocation.get('arguments', {}).get('title')
                if not title and isinstance(payload.get('input'), str):
                    match = re.search(r'\btitle\s*:\s*[\"\x27]([^\"\x27\n]{1,100})', payload['input'])
                    title = match.group(1) if match else None
                if title:
                    last_tool['operation'] = title
                calls.append(last_tool)
            if payload.get('type') == 'message' and payload.get('role') == 'assistant' and payload.get('channel') in {'commentary', 'final'}:
                text = '\n'.join(part.get('text', '') for part in payload.get('content', []) if part.get('type') in {'output_text', 'text'})
                last_message = {'at': entry.get('timestamp'), 'channel': payload.get('channel'), 'text': text[:2000]}
    state = {'pid': session['pid'], 'identity_matches': process_identity(session['pid']) == session['identity'],
             'durable_rollout_found': len(matches) == 1, 'tool_activity_records': len(calls),
             'last_tool': last_tool, 'last_progress_message': last_message,
             'done': json.loads((run / 'done.json').read_text(encoding='utf-8')) if (run / 'done.json').is_file() else None}
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
