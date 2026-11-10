from pathlib import Path
N=Path(__file__).resolve().parents[1]
def member_name(path):return path.relative_to(N).as_posix()
def main():
    import datetime as dt,difflib,hashlib,importlib.util,json
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def save(p,v):
        with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
    assert not (N/'manifest.json').exists()
    spec=importlib.util.spec_from_file_location('metadata_prep_verify',N/'verification/verify_preparation.py')
    check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
    result=check.verify();save(N/'verification/offline-preparation-readback.json',result)
    old=N.parent/'e02-source13-native-metadata-20261107-r1'
    for name in ('harness/adapter.py','code/bindings.py','code/entry.py'):
        delta=''.join(difflib.unified_diff((old/name).read_text('utf8').splitlines(keepends=True),(N/name).read_text('utf8').splitlines(keepends=True),fromfile='previous/'+name,tofile='current/'+name))
        (N/'verification'/(name.replace('/','-')+'.diff')).write_text(delta,encoding='utf8')
    (N/'plan.md').write_bytes((N.parents[4]/'docs/plans/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107.md').read_bytes())
    members=set()
    for directory in ('harness','inputs','tests','verification'):
        members.update(p for p in (N/directory).rglob('*') if p.is_file())
    members.update(N/'code'/name for name in ('entry.py','bindings.py'))
    for run in list((N/'offline').iterdir())+list((N/'code').glob('harness-preparation-*')):
        if not run.is_dir():continue
        members.update(p for p in run.iterdir() if p.is_file())
        for directory in ('snapshot','harness-source','harness'):
            members.update(p for p in (run/directory).rglob('*') if p.is_file())
    members.update(N/name for name in ('plan.md','execution-proposal.md','preparation-report.md'))
    value=dict(kind='SOURCE13_REAL_CONTROLLED_PREPARATION',candidate=result['candidate'],model='qwen3-8b-uncensored',
        model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',actual_released=False,test_count=result['tests'],
        prepared_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files={member_name(p):sha(p) for p in sorted(members)})
    save(N/'manifest.json',value);print(json.dumps(dict(manifest_sha256=sha(N/'manifest.json'),members=len(members),tests=result['tests'])))
if __name__=='__main__':main()
