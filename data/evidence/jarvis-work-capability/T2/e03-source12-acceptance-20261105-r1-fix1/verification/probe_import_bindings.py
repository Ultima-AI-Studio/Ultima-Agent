"""Read-only import/path/source probe; deliberately never inspect/start/product."""
import ast
import datetime as dt
import hashlib
import importlib
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'code'))
from acceptance_backend import AcceptanceBackend
from acceptance_entry import CASE, HEAD, MODEL

backend=AcceptanceBackend(root)
controller=backend.controller
assert controller.P==root/'code'
assert controller.old.PROTECTED_BASELINE==root/'inputs/protected-baseline.json'
assert controller.MODEL==MODEL
assert not (root/'code/inputs.json').exists()
assert controller.fixture_command(root/'actual'/CASE)==[
    '-B',str(root/'code/fixture_adapter.py'),'--fixture',str(root/'actual'/CASE),
    '--candidate-root',str(controller.ROOT)]
assert len(controller.old.protected_entries(backend.baseline))==7
source=controller.candidate_guard.verify_current_candidate()
assert source['candidate']==HEAD
sys.path.insert(0,str(controller.ROOT))
harness=importlib.import_module('src.brain.tests.work_context_acceptance')
assert Path(harness.__file__).resolve()==(controller.ROOT/'src/brain/tests/work_context_acceptance.py').resolve()
syntax=[]
for directory in ('code','preparation-support'):
    for path in sorted((root/directory).glob('*.py')):
        ast.parse(path.read_text(encoding='utf-8-sig'))
        syntax.append({'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
record={'status':'PASS_READONLY_BINDINGS','checked_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
        'source':source,'python_ast':syntax,'fixture_utf16_units':len(harness.CASES['e03']['text'].encode('utf-16le'))//2,
        'controller_source_check_called':False,'native_inspect_called':False,'ui_product_model_audio_actions':0,
        'actual_absent':not (root/'actual').exists(),'release_absent':not (root/'release').exists()}
with (root/'verification/import-binding-readback-fix1.json').open('x',encoding='utf-8',newline='\n') as stream:
    json.dump(record,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'status':record['status'],'python_ast':len(syntax),'candidate':source['candidate'],
                  'source_file_count':source['source_file_count'],'fixture_utf16_units':record['fixture_utf16_units'],
                  'actual_absent':record['actual_absent'],'release_absent':record['release_absent']}))
