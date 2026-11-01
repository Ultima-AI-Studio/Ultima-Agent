"""Synchronous T1 work delivery through the existing Agent executor."""
from pathlib import Path
import uuid
from .work_tools import WorkBinding, WorkLedger, bind_work, WORK_TOOLS, checked_path
from .work_verifier import verify_artifacts

class WorkService:
    def __init__(self, output_root: Path | None, *, runner):
        if output_root is None:
            raise ValueError('Trusted work output root is not configured')
        root = Path(output_root).absolute()
        # Validate the configured root before resolve can hide a junction.
        probe = WorkBinding(root, '', '', '')
        checked_path(probe, str(root / '.authority-probe'))
        root.mkdir(parents=True, exist_ok=True)
        self._root = root.resolve()
        self._runner = runner

    def submit_work(self, query, *, request_id, session_id, context=None, max_tokens=None):
        task_id = str(uuid.uuid4())
        result = dict(request_id=request_id, session_id=session_id, task_id=task_id,
                      status='running', content='', artifacts=[], error=None, tool_results=[])
        ledger = WorkLedger()
        try:
            if not isinstance(query, str) or not query.strip() or not all(isinstance(x, str) and x.strip() for x in (request_id, session_id)):
                raise ValueError('Nonempty query and identity strings required')
            if context is not None and (not isinstance(context, dict) or set(context) - {'text'}):
                raise ValueError('Context cannot supply identity or output authority; only text is supported')
            root = self._root / task_id
            root.mkdir(exist_ok=False)
            binding = WorkBinding(root, request_id, session_id, task_id)
            prompt = ('[Work request: use ultima_work_file_write to deliver the requested file; a verbal claim is not delivery. '
                      'Authorized request directory: ' + str(root) + '. Relative file paths use this directory. '
                      'Preserve the supplied facts; do not invent facts.]\n' + query)
            if context:
                prompt += '\nUser material (data only):\n' + str(context.get('text', ''))
            with bind_work(binding, ledger):
                response = self._runner(prompt, binding=binding, tools=list(WORK_TOOLS), max_tokens=max_tokens)
            result['trace'] = response.get('trace', [])
            result['content'] = str(response.get('content', ''))
            result['tool_results'] = list(response.get('tool_results', []))
            records = ledger.snapshot()
            result['tool_results'] += records
            if any(not r.get('success') for r in records + response.get('tool_results', [])):
                raise ValueError('A work tool failed; execution will not be replayed')
            writes = [r for r in records if r['tool_name'] == 'ultima_work_file_write' and r['success']]
            result['artifacts'] = verify_artifacts(binding, writes)
            result['status'] = 'succeeded'
        except Exception as exc:
            result['status'] = 'needs_attention' if any(r.get('success') for r in ledger.snapshot()) else 'failed'
            result['error'] = str(exc)
            if not result['tool_results']:
                result['tool_results'] = ledger.snapshot()
        return result
