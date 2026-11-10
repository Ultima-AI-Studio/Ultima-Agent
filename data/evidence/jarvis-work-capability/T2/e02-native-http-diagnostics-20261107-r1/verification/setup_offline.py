"""Prepare only offline checkers and verify pinned compatibility evidence."""
from pathlib import Path
import datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];P=N.parent/'e02-unique-sections-20261107-r1'
C='C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fresh(p,b):
    with p.open('xb') as f:f.write(b)
fresh(N/'inputs/accepted-dependency-pins.json',(P/'inputs/input-manifest.json').read_bytes())
body=(P/'verification/product_pytest.py').read_text('utf8').replace('jarvis-e02-unique-sections/UltimaAgent','jarvis-e02-http-diagnostics/UltimaAgent').replace("inputs/input-manifest.json","inputs/accepted-dependency-pins.json")
fresh(N/'verification/product_pytest.py',body.encode())
body=(P/'verification/run_product_checks.py').read_text('utf8').replace('jarvis-e02-unique-sections/UltimaAgent','jarvis-e02-http-diagnostics/UltimaAgent')
body=body.replace("GROUPS={'clock-red':","GROUPS={'http-red':['test_work_http_failure_diagnostics.py'],'http-green':['test_work_http_failure_diagnostics.py'],'clock-red':")
body=body.replace("paths += [N/'verification/grammar_checks.py', *sorted((N/'verification/upstream').glob('*')), *sorted((N/'verification/fixtures').glob('*'))]","paths += [N/'inputs/accepted-dependency-pins.json']")
fresh(N/'verification/run_product_checks.py',body.encode())
provenance=json.loads((N/'research/upstream/provenance.json').read_bytes())
provenance['files'] += [
    dict(file='chat-auto-parser-generator.cpp',url='https://github.com/ggml-org/llama.cpp/blob/b10488/common/chat-auto-parser-generator.cpp',expected_git_blob_sha1='af84ff323daf5d453e87cc3566d32f3f1d52bdeb',expected_bytes=23979),
    dict(file='gguf.h',url='https://github.com/ggml-org/llama.cpp/blob/b10488/ggml/include/gguf.h',git_blob_reference_independently_available=False)]
for name in ['ollama-v0.32.15-LLAMA_CPP_VERSION','ollama-v0.32.15-CMakeLists.txt']:
    source=P/'verification/upstream'/name;fresh(N/'research/upstream'/name,source.read_bytes())
    provenance['files'].append(dict(file=name,inherited_from=str(source),inherited_sha256=sha(source),url='https://github.com/ollama/ollama/blob/v0.32.15/'+('LLAMA_CPP_VERSION' if name.endswith('LLAMA_CPP_VERSION') else 'llama/server/CMakeLists.txt')))
for v in provenance['files']:
    raw=(N/'research/upstream'/v['file']).read_bytes()
    v.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),computed_git_blob_sha1=hashlib.sha1(('blob '+str(len(raw))+'\\0').encode().replace(b'\\0',b'\x00')+raw).hexdigest())
    if 'expected_bytes' in v:assert v['expected_bytes']==len(raw)
    if 'expected_git_blob_sha1' in v:assert v['expected_git_blob_sha1']==v['computed_git_blob_sha1']
provenance['recorded_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
provenance['installed_binary_equivalence_proven']=False
(N/'research/upstream/provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
fresh(N/'verification/offline-setup.json',json.dumps(dict(kind='OFFLINE_GUARD_PREPARATION_ONLY',source_guard=str(P/'verification/product_pytest.py'),source_guard_sha256=sha(P/'verification/product_pytest.py'),dependency_pins_sha256=sha(N/'inputs/accepted-dependency-pins.json'),candidate=C,actual_cases=0,model_calls=0,service_operations=0),indent=2).encode())
print('Prepared guarded offline runners and '+str(len(provenance['files']))+' fixed-source records')
