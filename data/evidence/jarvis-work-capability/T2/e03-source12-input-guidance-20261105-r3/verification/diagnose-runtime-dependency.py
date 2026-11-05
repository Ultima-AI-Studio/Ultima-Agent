"""Read files/AST only. Never import or execute product modules or touch UI/model."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import difflib
import hashlib
import json
import subprocess

MAIN = Path(r'H:\UltimaAI\UltimaAgent')
RUNTIME = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-r25-runtime-complete')
HERE = Path(__file__).resolve().parent
MANIFEST = MAIN / 'data/evidence/jarvis-work-capability/T2/e03-source12-20261105-r31-preflight-log-isolation/candidate-manifest-r13.json'


def info(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
inputs = [Path(p) for p in manifest['source_files']]
module = MAIN / 'src/brain/environment_upgrade.py'
tree = ast.parse(module.read_bytes())
environment = RUNTIME / 'src/brain/environment.py'
definitions = {n.name for n in ast.parse(environment.read_bytes()).body if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
required = ['EnvironmentSnapshot', 'capture_snapshot', 'scan_hardware', 'scan_disks', 'scan_apps']
tracking = subprocess.run(['git', '-C', str(MAIN), 'ls-files', '--', 'src/brain/environment_upgrade.py'], capture_output=True, text=True, check=True).stdout
status = subprocess.run(['git', '-C', str(MAIN), 'status', '--short', '--untracked-files=all', '--', 'src/brain/environment_upgrade.py'], capture_output=True, text=True, check=True).stdout.strip()
code = RUNTIME / 'src/brain/work_service.py'
before = code.read_text(encoding='utf-8')
anchor = "            result['error'] = str(exc)\n"
assert before.count(anchor) == 1
addition = ("            result['content'] = ('本次任务未完成，部分操作可能已生效，请核对结果。'\n"
            "                                 if effects else '本次任务未完成。')\n")
after = before.replace(anchor, anchor + addition)
diff = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='a/src/brain/work_service.py', tofile='b/src/brain/work_service.py'))
diff += ''.join(difflib.unified_diff([], module.read_text(encoding='utf-8').splitlines(keepends=True), fromfile='/dev/null', tofile='b/src/brain/environment_upgrade.py'))
(HERE / 'source13-proposed-change.diff').write_text(diff, encoding='utf-8', newline='\n')
receipt = dict(
    recorded_at=datetime.now(timezone.utc).isoformat(),
    method='Static UTF-8 source, standard-library AST/hash and readonly Git inspection only. No product import, execution or tests.',
    candidate=manifest['candidate'], candidate_manifest=info(MANIFEST),
    call_chain=[
        dict(file='src/brain/work_tools.py', line=577, statement='from .exec.channel import LocalExecChannel', observation='Inside WorkReplaceTool.run before capture/channel registration/before_send.'),
        dict(file='src/brain/exec/channel.py', line=26, statement='from ..environment_upgrade import scan_processes', observation='Unconditional module-level import.'),
        dict(file='src/brain/environment_upgrade.py', observation='Absent from pinned runtime and candidate source_files inventory; present but untracked in main project.')
    ],
    existing_module=info(module), existing_module_git_status=status, existing_module_tracked=bool(tracking.strip()),
    runtime_module_exists=(RUNTIME / 'src/brain/environment_upgrade.py').exists(),
    module_in_manifest=any(p.name == 'environment_upgrade.py' for p in inputs),
    candidate_source_entries=len(inputs),
    existing_module_relative_imports=[ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.level],
    runtime_environment=info(environment), required_environment_names=required,
    missing_environment_names=sorted(set(required)-definitions),
    local_dependency_chain_static_result='The missing module imports only existing .environment names plus standard-library modules; no further missing local module on this specific chain.',
    general_closure_not_proven=True,
    process_scan_note='scan_processes is defined on import; it calls PowerShell only if invoked. WorkReplaceTool supplies an approved-target observer. Static reading is not execution proof.',
    failure_content=dict(file=info(code), assigned_model_content_line=98, rejected_tool_line=106, exception_status_line=151, exception_error_line=152, observation='The except branch changes status/error but retains model content assigned earlier; the actual failed case therefore exposes a success claim.'),
    proposed_change=info(HERE / 'source13-proposed-change.diff'),
    proposal_applied=False, product_source_changed=False, tests_executed=False, actual_cases_started=0,
    limitations=['No dynamic import resolution verified.', 'No guarantee of general model reliability from one correct draft.', 'Fresh source candidate and runtime package must be reviewed before another separately allocated actual case.', 'Original terminal, candidate, source files and sealed evidence remain unchanged.']
)
(HERE / 'runtime-dependency-diagnosis.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
print(json.dumps({k:receipt[k] for k in ['candidate','runtime_module_exists','module_in_manifest','candidate_source_entries','missing_environment_names','proposal_applied','product_source_changed','tests_executed','actual_cases_started']}, ensure_ascii=True))
