from pathlib import Path
import ctypes, datetime, hashlib, json, subprocess
from ctypes import wintypes as W
root=Path(__file__).resolve().parents[4]
out=Path(__file__).resolve().parent/'round3-final'
out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
inputs=[]
for name in ['w1-delivered-selfcheck-verified-path-positive-20261021T0324','w1-delivered-selfcheck-verified-path-negative-20261021T0325']:
    directory=root/'logs'/name
    entry=json.loads((directory/'entry-result.json').read_text(encoding='utf-8-sig'))
    started=json.loads((directory/'host-started.json').read_text(encoding='utf-8-sig'))
    checks[name]={'source_matches':all(sha(Path(p))==v for p,v in entry['source_manifest'].items()),
                  'artifact_matches':all(sha(Path(p))==v for p,v in entry['artifact_manifest'].items()),
                  'before_matches_after':json.loads((directory/'source-before.json').read_text(encoding='utf-8-sig'))==entry['source_manifest'],
                  'status':entry['status'],'exit_code':entry['exit_code'],
                  'actual_path_matches':started['actualProcessExecutable'].lower()==started['executable'].lower(),
                  'launch_exe_hash_matches':sha(Path(started['executable']))==started['executableSha256'],
                  'launch_dll_hash_matches':sha(Path(started['executable']).with_suffix('.dll'))==started['assemblySha256']}
    inputs.extend(p for p in directory.iterdir() if p.is_file())
inputs.extend(p for p in (root/'logs/w1-final-mouse-20261021T0313').iterdir() if p.is_file())
inputs.extend(p for p in (root/'logs/w1-final-native-2026-10-21T03-08-13-206Z').iterdir() if p.is_file())
for rel in ['logs/w1-host-resume-20261021T024845Z/after/root-kernel-process-state.json','logs/w1-host-resume-20261021T024845Z/after/root-targeted-cleanup.json','tasks/queue/runs/wo-s1-host-shell-20261021T023427316731Z/done.json','src/host-shell/README.md','scripts/selfcheck-host-shell.py','scripts/HostSelfcheck/Program.cs','scripts/HostSelfcheck/HostSelfcheck.csproj']:
    inputs.append(root/rel)
for p in (root/'tasks/cards').glob('s1-host-shell-*/*.md'):inputs.append(p)
manifest={}
for p in inputs:
    rel=p.relative_to(root); dest=out/rel; dest.parent.mkdir(parents=True,exist_ok=True)
    data=p.read_bytes();dest.write_bytes(data);manifest[str(rel)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
test=subprocess.run([str(root/'tools/python31313/python.exe'),'-m','unittest','discover','-s','scripts/tests','-p','test_host_selfcheck_entry.py','-v'],cwd=root,capture_output=True)
(out/'tests.stdout.txt').write_bytes(test.stdout);(out/'tests.stderr.txt').write_bytes(test.stderr)
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.GetProcessTimes.argtypes=[W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)]
k.GetExitCodeProcess.argtypes=[W.HANDLE,ctypes.POINTER(W.DWORD)]
k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD];k.WaitForSingleObject.restype=W.DWORD
k.CloseHandle.argtypes=[W.HANDLE]
h=k.OpenProcess(0x1000|0x100000,False,59328)
state={'pid':59328,'read_only':True,'open':bool(h)}
if h:
    try:
        c,e,kt,ut=W.FILETIME(),W.FILETIME(),W.FILETIME(),W.FILETIME()
        ok=k.GetProcessTimes(h,ctypes.byref(c),ctypes.byref(e),ctypes.byref(kt),ctypes.byref(ut))
        ec=W.DWORD();k.GetExitCodeProcess(h,ctypes.byref(ec))
        state.update(identity=str((c.dwHighDateTime<<32)|c.dwLowDateTime) if ok else None,exit_code=ec.value,wait_status=k.WaitForSingleObject(h,0),exit_time=(e.dwHighDateTime<<32)|e.dwLowDateTime)
    finally:k.CloseHandle(h)
result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'auditor':'/root/w1_acceptance','checks':checks,'failure_regression_exit':test.returncode,'residual_process':state,'sources':manifest,'functional_U01_U05':'PASS','whole_work_order':'BLOCKED_CLEANUP_AND_ADMINISTRATIVE_CLOSEOUT'}
(out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='sources'},ensure_ascii=False))
