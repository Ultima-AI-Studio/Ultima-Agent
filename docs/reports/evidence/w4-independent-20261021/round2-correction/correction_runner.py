from __future__ import annotations
import ctypes, difflib, hashlib, json, os, re, subprocess, sys, tempfile, time
from ctypes import wintypes as W
from pathlib import Path
ROOT=Path(r'H:\UltimaAI\UltimaAgent')
OUT=Path(__file__).resolve().parent
R1=OUT.parent/'round1'
OLD=ROOT/'docs/reports/evidence/text-loop-development-20261021/round1/source'
RUN=ROOT/'tasks/queue/runs/wo-s1-task-text-loop-20261021T044748126206Z'
sys.path.insert(0,str(ROOT));sys.dont_write_bytecode=True
from tasks.queue_engine.windows_runtime import WindowMonitor
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    with (OUT/name).open('x',encoding='utf-8') as f:
        f.write(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2))
def sealcheck():
    manifest=json.loads((R1/'evidence-sha256.json').read_text())
    return {'count':len(manifest),'mismatches':[n for n,h in manifest.items() if sha(R1/n)!=h],
            'manifest_sha256':sha(R1/'evidence-sha256.json')}
seal_before=sealcheck()
source_before={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (ROOT/'src/brain').rglob('*') if p.is_file() and p.suffix in ('.py','.md')}
diff=[]
for p in sorted((OLD/'src/brain').rglob('*')):
    if p.is_file():
        new=ROOT/p.relative_to(OLD)
        diff.extend(difflib.unified_diff(p.read_text(encoding='utf-8').splitlines(True),new.read_text(encoding='utf-8').splitlines(True),fromfile='original/'+str(p.relative_to(OLD)),tofile='current/'+str(p.relative_to(OLD))))
save('correction-source.diff',''.join(diff))
cards={}
for tid in ('s1-task-intent-parse','s1-task-queue-source','s1-task-aggregate-report'):
    old=(OLD/'tasks/cards'/tid/'task.md').read_bytes();new=(ROOT/'tasks/cards'/tid/'task.md').read_bytes()
    cards[tid]={'original_preserved_prefix':new.startswith(old),'old_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':hashlib.sha256(new).hexdigest()}
session=json.loads((RUN/'session.json').read_text());done=json.loads((RUN/'done.json').read_text());final=json.loads((RUN/'final.json').read_text())
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];kernel.OpenProcess.restype=W.HANDLE
kernel.CloseHandle.argtypes=[W.HANDLE]
kernel.GetProcessTimes.argtypes=[W.HANDLE,ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME),ctypes.POINTER(W.FILETIME)]
handle=kernel.OpenProcess(0x1000,False,session['pid']);current_identity=None;process_error=ctypes.get_last_error() if not handle else None
if handle:
    try:
        times=[W.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle,*[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        current_identity=str((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime)
    finally:kernel.CloseHandle(handle)
identity_gone=(not handle and process_error==87) or (current_identity is not None and current_identity!=session['identity'])
save('run-readback.json',{'session':session,'done':done,'final':final,'identity_probe':{'current_identity':current_identity,'open_process_error':process_error,'original_identity_gone':identity_gone},'cards':cards})
with (OUT/'review_checks.py').open('xb') as f:f.write((R1/'review_checks.py').read_bytes())
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT))
p=subprocess.run([sys.executable,'-B','-X','utf8',str(OUT/'review_checks.py')],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180,creationflags=subprocess.CREATE_NO_WINDOW)
save('independent-rerun-output.txt',p.stdout+'\n'+p.stderr)
checks=json.loads((OUT/'independent-results.json').read_text())
cli=[];monitor_result=None;monitor_error=None
with tempfile.TemporaryDirectory(prefix='ultima-w4-cli-') as raw:
    missing=Path(raw)/'missing-library'
    cases=[('normal-empty-production',['查任务状态'],0,'当前任务库为空'),
           ('negated-no-read',['--root',str(missing),'先不查任务状态'],0,''),
           ('missing-isolated-library',['--root',str(missing),'查任务状态'],2,'状态读取失败')]
    monitor=WindowMonitor(os.getpid()).start()
    try:
        time.sleep(.05)
        for name,args,code,prefix in cases:
            child=subprocess.Popen([sys.executable,'-B','-X','utf8',str(ROOT/'src/brain/cli.py'),*args],cwd=ROOT,env=env,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW)
            stdout,stderr=child.communicate(timeout=15)
            cli.append({'name':name,'pid':child.pid,'exit_code':child.returncode,'stdout':stdout,'stderr':stderr,
                'passed':child.returncode==code and not stderr and (stdout=='' if prefix=='' else stdout.startswith(prefix))})
            time.sleep(.05)
    finally:
        try:monitor_result=monitor.stop()
        except Exception as exc:monitor_error=repr(exc)
    cli_missing_uncreated=not missing.exists()
observed=monitor_result['observed_pids'] if monitor_result else []
window_ok=bool(monitor_result and monitor_result['samples']>0 and not monitor_result['visible_windows'] and not monitor_error and all(c['pid'] in observed for c in cli))
save('cli-window-observation.json',{'cases':cli,'monitor':monitor_result,'error':monitor_error,'all_child_pids_observed':all(c['pid'] in observed for c in cli),
    'missing_library_uncreated':cli_missing_uncreated,'passed':window_ok and all(c['passed'] for c in cli) and cli_missing_uncreated})
seal_after=sealcheck()
source_after={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in (ROOT/'src/brain').rglob('*') if p.is_file() and p.suffix in ('.py','.md')}
textlog=(OUT/'developer-text-tests.txt').read_text(encoding='utf-8')
text_count=int(re.search(r'Ran (\d+) tests',textlog)[1])
baseline=json.loads((OUT/'frozen-baseline-after.txt').read_text())
cmd=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
same_script=sha(OUT/'review_checks.py')==sha(R1/'review_checks.py')
important1=all(c['passed'] for c in checks['checks'] if c['name'].startswith('无明确指令不读库'))
important2=all(c['passed'] for c in checks['checks'] if c['name'].startswith('不完整库只读无目录创建'))
conditions={'original_checks_49_passed':checks['passed']==49 and checks['failed']==0,'text_16_passed':text_count==16 and 'OK' in textlog,
    'all_subprocess_runs_zero':all(r['returncode']==0 for r in checks['runs']),'positive_95_percent':checks['positive_rate']==.95,
    'unchanged_check_script':same_script,'important_1_fixed':important1,'important_2_fixed':important2,
    'window_observation_passed':window_ok and all(c['passed'] for c in cli) and cli_missing_uncreated,
    'lifecycle_completed':done.get('exit_code')==0 and done.get('receipt_valid') is True and done.get('parent_lost') is False and done.get('state')=='audit' and identity_gone,
    'round1_seal_preserved':seal_before==seal_after and not seal_after['mismatches'],
    'cards_append_only':all(v['original_preserved_prefix'] for v in cards.values()),
    'source_unchanged_during_review':source_before==source_after,'frozen_baseline':baseline['manifest_matching']==36 and baseline['production_tasks_unchanged'] and baseline['status']=='PASS',
    'head_unchanged':cmd.stdout.strip()=='da7323eed3243476986e4000589619d4b545fa28'}
result={'verdict':'PASS' if all(conditions.values()) else 'REVISE','scope':'既有两项Important纠正核对及指定CLI窗口验收',
    'independent_checks':{'passed':checks['passed'],'failed':checks['failed'],'total':len(checks['checks'])},'text_tests':{'passed':text_count,'failed':0 if 'OK' in textlog else None},
    'positive_holdout':{'matched':19,'total':20,'rate':checks['positive_rate']},'conditions':conditions,'important_issues':{'1_corrected':important1,'2_corrected':important2},
    'cli_zero_window':{'passed':conditions['window_observation_passed'],'samples':monitor_result['samples'] if monitor_result else None,'observed_pids':observed,
      'visible_windows':monitor_result['visible_windows'] if monitor_result else None,'error':monitor_error},'lifecycle':{'identity_gone':identity_gone,'done':done},
    'round1_seal':seal_after,'frozen_baseline':baseline,'source-manifest':source_after,'owner_approval':False,'v03_freeze_performed':False}
save('result.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
