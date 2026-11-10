"""Closed current8B preparation input contract. Never grants runtime authority."""
from pathlib import Path
import hashlib,json,re

N=Path(__file__).resolve().parents[1];T=N.parent;Q=T/'e02-source13-exact-probe-20261106'
C=Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e02-failure-state\UltimaAgent')
CANDIDATE='22653fb77445bad4f5b9d9ae789cd35972dcc984'
MODEL='qwen3-8b-uncensored'
DIGEST='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
CORPUS=T/'source6-native-reference/controlled-corpus-inputs/corpus.json'
CORPUS_SHA='9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002'
PROTECTED_BASELINE=T/'e02-source-reference-schema-20261107-r1/inputs/protected-baseline.json'
PROTECTED_BASELINE_SHA='1b7e945e9ce52e44b8b384fc5e3911b77b7da4d80beeba615f341bf3e923fce5'
CANDIDATE_MANIFEST=N/'inputs/candidate-runtime-manifest.json'
CANDIDATE_MANIFEST_SHA='3c275a694ff4969c55efd2470a54f149a629cdd79d660063b6c6753b1a9cc92c'
BUDGETS=dict(cli=1,search=1,GET=4,inspect=6,write=1,ACK=1,native_POST=8,service_seconds=260,
    client_seconds=300,work_seconds=275,cleanup_seconds=310,outer_seconds=315,retry=0)
FIELDS={'schema','kind','candidate','candidate_root','model','model_digest','model_manifest_path',
    'corpus_path','corpus_sha256','protected_baseline_path','protected_count','budgets','actual_released',
    'source_files','previous_plumbing','files'}
PLUMBING_FIELDS={'registration_path','registration_sha256','review_path','review_sha256','run_id','real_research_credit'}
ROLES=['ollama','brain_primary','brain_runtime_child','voice_primary','voice_runtime_child',
    'voice_listener_primary','voice_listener_runtime_child']

def require(ok,label):
    if not ok:raise ValueError(label)

def strict_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'Duplicate JSON key')
            result[key]=value
        return result
    def constant(value):raise ValueError('Nonfinite JSON number')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=constant)

def canonical_path(value):
    require(type(value) is str and bool(value),'Absolute path string required')
    p=Path(value)
    require(p.is_absolute() and '..' not in p.parts and str(p)==value,'Canonical absolute path required')
    require(':' not in value[2:],'Alternate stream path refused')
    return p

def is_sha(value):return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None

def validate(value: dict, *, read_bytes):
    require(type(value) is dict and set(value)==FIELDS,'Closed preparation input fields')
    require(type(value['schema']) is int and value['schema']==1,'Input schema')
    require(value['kind']=='SOURCE13_CURRENT8B_REAL_CONTROLLED_PREPARATION','Real controlled preparation kind')
    require(value['candidate']==CANDIDATE and value['candidate_root']==str(C),'Current source13 candidate required')
    require(value['model']==MODEL and value['model_digest']==DIGEST,'Only current community8B allowed')
    require(value['actual_released'] is False,'Preparation cannot release actual runtime')
    require(type(value['protected_count']) is int and value['protected_count']==7,'Seven protected identities required')
    budgets=value['budgets']
    require(type(budgets) is dict and set(budgets)==set(BUDGETS)
        and all(type(budgets[k]) is int and budgets[k]==v for k,v in BUDGETS.items()),'Original exact budgets required')
    require(value['corpus_path']==str(CORPUS) and value['corpus_sha256']==CORPUS_SHA,'Original question and four sources required')
    require(value['model_manifest_path']==str(Path(r'C:\Users\Administrator\.ollama\models\manifests\registry.ollama.ai\library')/MODEL/'latest'),
        'Original local model manifest required')
    require(value['protected_baseline_path']==str(PROTECTED_BASELINE),'Current accepted protected baseline required')
    files=value['files'];sources=value['source_files'];prior=value['previous_plumbing']
    require(type(files) is dict and bool(files) and type(sources) is dict and bool(sources),'Bound files and source inventory required')
    require(type(prior) is dict and set(prior)==PLUMBING_FIELDS,'Closed prior plumbing fields')
    require(type(prior['real_research_credit']) is int and prior['real_research_credit']==0,'Mock plumbing is not real research credit')
    require(prior['run_id']=='a47c74c4-58e7-4a63-ad7d-f63be9c17a51','Current independently reviewed plumbing result required')
    for key,expected in [('registration_path',Q/'execution/result-registration.json'),('review_path',Q/'review/independent-exact-probe-result-review.json')]:
        require(prior[key]==str(expected),'Fixed prior result path')
    required={str(PROTECTED_BASELINE):PROTECTED_BASELINE_SHA,str(CANDIDATE_MANIFEST):CANDIDATE_MANIFEST_SHA,value['model_manifest_path']:DIGEST,
        str(CORPUS):CORPUS_SHA,prior['registration_path']:prior['registration_sha256'],prior['review_path']:prior['review_sha256']}
    for path,digest in {**required,**sources}.items():
        require(is_sha(digest) and files.get(path)==digest,'Missing or conflicting required binding')
    require(value['protected_baseline_path'] in files,'Unbound protected baseline')
    # Validate all path/hash shapes before asking a reader to touch any file.
    for path,digest in files.items():canonical_path(path);require(is_sha(digest),'SHA256 string required')
    blobs={}
    for path,digest in files.items():
        try:raw=read_bytes(Path(path))
        except (OSError,KeyError) as exc:raise ValueError('Missing bound input: '+path) from exc
        require(type(raw) is bytes and hashlib.sha256(raw).hexdigest()==digest,'Input bytes changed: '+path)
        blobs[path]=raw
    candidate=strict_json(blobs[str(CANDIDATE_MANIFEST)])
    require(candidate['candidate']==CANDIDATE and candidate['source_files']==sources,'Current full candidate inventory required')
    baseline=strict_json(blobs[value['protected_baseline_path']])
    protected=baseline.get('protected5',[])+baseline.get('protected_listener_pair',[])
    require(baseline.get('protected_process_count')==7 and [r.get('role') for r in protected]==ROLES,'Protected role inventory mismatch')
    require(len({r['pid'] for r in protected})==7,'Duplicate protected process')
    for row in protected:
        require(all(type(row.get(k)) is int and row[k]>0 for k in ('pid','parent_pid','created_filetime')),'Protected creation identity required')
        canonical_path(row.get('exe'));require(is_sha(row.get('command_line_sha256')),'Protected command binding required')
    registration=strict_json(blobs[prior['registration_path']]);review=strict_json(blobs[prior['review_path']])
    require(registration['run_id']==review['run_id']==prior['run_id'] and registration['actual_research_credit']==0,'Prior result binding')
    require(registration['execution']==review['verdict']=='PASS_ZERO_INFERENCE_PLUMBING_ONLY'
        and review['reviewer']=='root-independent' and review['real_research_acceptance_credit'] is False,'Independent plumbing credit boundary')
    require(registration['review_sha256']==prior['review_sha256'],'Prior result review hash')
    return value

def load_inputs(path: Path):
    return validate(strict_json(path.read_bytes()),read_bytes=Path.read_bytes)
