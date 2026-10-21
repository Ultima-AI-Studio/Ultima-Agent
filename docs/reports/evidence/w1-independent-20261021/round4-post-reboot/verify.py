import ctypes, hashlib, json, subprocess
from pathlib import Path
from datetime import datetime, timezone
R=Path('H:/UltimaAI/UltimaAgent'); O=Path(__file__).parent
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(name,obj):
    with (O/name).open('x',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2)
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]; k.OpenProcess.restype=ctypes.c_void_p
h=k.OpenProcess(0x1000|0x100000,False,59328)
native={'pid':59328,'expected_creation_identity':134370250506523457,'handle':bool(h),'open_error':ctypes.get_last_error(),'at':datetime.now(timezone.utc).isoformat()}
if h:
    times=[ctypes.c_ulonglong() for _ in range(4)]
    k.GetProcessTimes.argtypes=[ctypes.c_void_p]+[ctypes.c_void_p]*4
    native['times_ok']=bool(k.GetProcessTimes(h,*[ctypes.byref(x) for x in times])); native['creation']=times[0].value
    k.CloseHandle.argtypes=[ctypes.c_void_p]; k.CloseHandle(h)
dump('independent-native-process.json',native)
runs=[]; sm={}; issues=[]
for mode,stamp,expected,exitcode in [('positive','0400','PASS',0),('negative','0401','FAIL',1)]:
    d=R/f'logs/w1-post-reboot-final-{mode}-20261021T{stamp}'
    e=read(d/'entry-result.json'); r=read(d/'result.json'); b=read(d/'source-before.json'); host=read(d/'host-started.json')
    mismatch=[p for p,v in e['source_manifest'].items() if sha(p)!=v]
    amismatch=[p for p,v in e['artifact_manifest'].items() if sha(p)!=v]
    preserve=r['processPreservation']; ids=lambda a:{v['Identity'] for v in a}
    q={'mode':mode,'entry_status':e['status'],'exit_code':e['exit_code'],'source_mismatch':mismatch,'artifact_mismatch':amismatch,'source_before_equals_after':b==e['source_manifest'],'source_stable_claim':e['sources_unchanged_during_build_and_run'],'path_readback_matches':host['actualProcessExecutable']==host['executable'],'exe_hash_matches':sha(host['executable'])==host['executableSha256'],'dll_hash_matches':sha(Path(host['executable']).with_suffix('.dll'))==host['assemblySha256'],'background_identity_count':len(preserve['before']),'background_identity_preserved':ids(preserve['before'])<=ids(preserve['after']),'unexpected_windows':len(e['unexpected_windows']),'chain':r['chain']}
    q['passed']=e['status']==expected and e['exit_code']==exitcode and not mismatch and not amismatch and q['source_before_equals_after'] and q['path_readback_matches'] and q['exe_hash_matches'] and q['dll_hash_matches'] and q['background_identity_preserved'] and not q['unexpected_windows']
    runs.append(q); sm.update(e['source_manifest'])
    for p in d.iterdir():
        if p.is_file():
            target=O/mode/p.name; target.parent.mkdir(exist_ok=True)
            with target.open('xb') as f:f.write(p.read_bytes())
sm[str(R/'src/host-shell/README.md')]=sha(R/'src/host-shell/README.md')
w2=read(R/'docs/reports/evidence/w2-20261021/round2/source-manifest.json'); core={p:v for p,v in w2.items() if '/tasks/queue_engine/' in p.replace('\\','/') or '/tasks/tests/' in p.replace('\\','/')}
w2bad=[p for p,v in core.items() if sha(p)!=v]
cards={}
for d in sorted((R/'tasks/cards').glob('s1-host-shell-*')):
    cards[d.name]={}
    for n in ['completion.md','acceptance-evidence.md','landed-files.md']:
        p=d/n; t=p.read_text(encoding='utf-8-sig'); cards[d.name][n]={'exists':True,'sha256':sha(p),'formal_entry_added':'selfcheck-host-shell.py' in t,'post_reboot_added':'post-reboot' in t}
before=read(R/'logs/maintenance/w1-restart-20261021/before.json'); markers=[{'path':x['path'],'hash_matches':sha(x['path'])==x['sha256'],'token_present':before['maintenance_token'] in Path(x['path']).read_text()} for x in before['dispatch_markers']]
adapter=read(R/'tasks/queue/runs/wo-s1-host-shell-20261021T023427316731Z/done.json')
cleanup=not h and native['open_error']==87
result={'at':datetime.now(timezone.utc).isoformat(),'technical_W1_pass':all(q['passed'] for q in runs),'cleanup_gate_pass':cleanup,'may_create_internal_tag':cleanup and all(q['passed'] for q in runs) and not w2bad,'owner_freeze_approved':False,'source_manifest':sm,'runs':runs,'W2_core_count':len(core),'W2_core_unchanged':not w2bad,'W2_mismatch':w2bad,'cards':cards,'markers':markers,'adapter_preserved':adapter,'tags':subprocess.check_output(['git','tag','--list'],cwd=R,text=True).splitlines(),'scope':'independent read-only runtime/source audit; may_create_internal_tag permits subsequent administrative closeout and does not assert tag exists'}
dump('result.json',result)
print(json.dumps({k:result[k] for k in ['technical_W1_pass','cleanup_gate_pass','may_create_internal_tag','W2_core_count','W2_core_unchanged','cards','tags']},ensure_ascii=False,indent=2))
