$ErrorActionPreference='Stop'
$root='H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-native-write-diagnostics-20261107-r1'
$python='H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe'
if(Test-Path -LiteralPath (Join-Path $root 'release')) { throw 'This case already has release state; never retry' }
$checkpoint=Get-Content -LiteralPath (Join-Path $root 'verification\ready-checkpoint.json') -Raw | ConvertFrom-Json -AsHashtable
$head=(& git -C 'H:\UltimaAI\UltimaAgent' rev-parse HEAD).Trim()
if($head -ne $checkpoint.main.commit) { throw 'Preparation checkpoint HEAD changed' }
@'
from pathlib import Path
import datetime as dt,importlib.util,json,os
N=Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-native-write-diagnostics-20261107-r1')
spec=importlib.util.spec_from_file_location('grant_readiness',N/'code/entry.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
ready=e.read_ready(N)
assert e.CANDIDATE=='6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696'
scope=e.load(N/'inputs/granted-scope.json')
assert scope['question_id']=='call_948abbc3ba2948a9b3441d57051d9b27'
assert scope['conditional_actual_case_allocation']==scope['result_review_allocation']==1 and scope['retry']==0
assert not (N/'release').exists() and not (N/'actual').exists()
issued=dt.datetime.now(dt.timezone.utc)
grant=dict(schema=1,kind=e.KIND,source='user_explicit',question_id=scope['question_id'],answer=scope['answer'],
    candidate=e.CANDIDATE,model=e.MODEL,model_digest=e.DIGEST,manifest_sha256=ready['manifest_sha256'],review_sha256=ready['review_sha256'],
    case='E02-controlled-1',actual_case_allocation=1,result_review_allocation=1,retry=0,
    issued_at=issued.isoformat(),expires_at=(issued+dt.timedelta(seconds=120)).isoformat())
(N/'release').mkdir()
e.save_new(N/'release/user-allocation.json',grant)
print(json.dumps(dict(grant_created=True,question_id=scope['question_id'],manifest_sha256=ready['manifest_sha256'])))
'@ | & $python -I -B -X utf8 -
if($LASTEXITCODE -ne 0) { throw 'Fresh allocation creation failed; entry was not invoked' }
$statePath='H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\current-run.json'
$state=Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json -AsHashtable
$state.phase='SOURCE15_E02_WRITE_DIAGNOSTICS_AUTHORIZED_SINGLE_EXECUTION'
$state.workflow_status='executing_authorized_single_case'
$state.e02_execution_released=$true
$state.live_gate_released=$true
$state.next_action_scope.authority_issued=$true
[IO.File]::WriteAllText($statePath,($state | ConvertTo-Json -Depth 60)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
$start=[DateTimeOffset]::UtcNow
$timer=[Diagnostics.Stopwatch]::StartNew()
& $python -I -B -X utf8 (Join-Path $root 'code\entry.py') 1> (Join-Path $root 'release\entry.stdout.log') 2> (Join-Path $root 'release\entry.stderr.log')
$exitCode=$LASTEXITCODE
$timer.Stop()
$result=[ordered]@{entry='code/entry.py';argv=@($python,'-I','-B','-X','utf8',(Join-Path $root 'code\entry.py'));started_utc=$start.ToString('o');finished_utc=[DateTimeOffset]::UtcNow.ToString('o');outer_elapsed_seconds=$timer.Elapsed.TotalSeconds;exit_code=$exitCode;invocations=1;retry=0;question_id='call_948abbc3ba2948a9b3441d57051d9b27'}
$target=Join-Path $root 'release\tool-execution-receipt.json'
$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result | ConvertTo-Json -Depth 5)+[Environment]::NewLine)
$stream=[IO.File]::Open($target,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
try { $stream.Write($bytes,0,$bytes.Length);$stream.Flush($true) } finally { $stream.Dispose() }
[ordered]@{exit_code=$exitCode;outer_elapsed_seconds=$timer.Elapsed.TotalSeconds;receipt=$target} | ConvertTo-Json -Compress
exit $exitCode
