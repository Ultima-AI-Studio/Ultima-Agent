from pathlib import Path
N=Path(__file__).resolve().parents[1]
def member_name(path):
    return path.relative_to(N).as_posix()

def main():
    import datetime as dt,difflib,hashlib,importlib.util,json
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    def save(p,v):
        with p.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
    assert not (N/'manifest.json').exists() and not (N/'release').exists() and not (N/'actual').exists()
    spec=importlib.util.spec_from_file_location('recovery_readback',N/'verification/verify_recovery.py')
    check=importlib.util.module_from_spec(spec);spec.loader.exec_module(check)
    result=check.verify();save(N/'verification/offline-recovery-readback.json',result)
    old=N.parent/'e02-source13-real-controlled-preparation-20261107-r1'
    for name in ('adapter.py','test_adapter.py','run_checks.py'):
        before=(old/'harness'/name).read_text('utf8').splitlines(keepends=True)
        after=(N/'harness'/name).read_text('utf8').splitlines(keepends=True)
        (N/'verification'/(name+'.diff')).write_text(''.join(difflib.unified_diff(before,after,fromfile='preserved/'+name,tofile='recovery/'+name)),encoding='utf8')
    plan=N.parents[4]/'docs/plans/jarvis-work-e02-source13-child-admission-recovery-proposal-20261107.md'
    (N/'plan.md').write_bytes(plan.read_bytes())
    corpus=json.loads((N.parent/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())
    proposal=f'''# 已授权的子进程准入恢复单例

原工单wo-ultimaagent-20261101-0021 / T2。用户call_42e3d2dd124f406cb3ccebd14a9b1c0f已明确授权最小补修、离线验证和必要独审；仅准备审查PASS后，运行一次当前8B原题四来源研究并独立复核，失败不重试。授权范围原文保存于inputs/granted-scope.json，不再请求相同授权。

产品候选269aca511d88412dbb9c15d23911138469a37aa2；仅qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题：{corpus['query']}

唯一命令：
```powershell
& 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Scripts\\python.exe' -I -B -X utf8 '{N/'code/entry.py'}'
```

独立准备PASS、本地提交/tag及文档镜像完成后，才创建release/user-allocation.json，绑定本manifest、准备review、本用户问题编号和原答复，TTL120秒；入口独占消费。实际例1、结果复核1、retry0。保持原RootInvocation父时钟，CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300及work275/cleanup310/seal315秒。

浏览器搜索/GET仅使用原四份完整受控来源，原SDK/HTTPX模型调用保持真实。当前补修只拆分父/子准入核验职责：子端不再启动CIM查询辅助进程，仍核对7个当前原生身份及封存证明；父端在启动前和实际CLI提交前保留完整native/CIM/parent/命令摘要核验。清理与未知后代拒绝规则保持。无UI、音频或生产服务操作；只管理本例已确认的新进程。原正常SDK SSRF分支可能对raw.githubusercontent.com作受限DNS。

写域为本目录的release、controller-authority、controller-ledger.json、native-preflight、actual/E02-controlled-1及随后review/verification。前轮7530ef7f-ad0b-4151-bf2f-800c54ac9449的FAIL/清理FAIL和所有旧证据原样保留，新目录不重置历史。产出须经真实首结果、四来源/引用、SDK packet、research.md写入/ACK与两次读回、原时限和清理门；机械通过仍待只读独立事实复核。

最多增加E02受控1/3；同候选后续两例及真实联网至少3条去重来源仍有各自原门。当前E02/T2未过，E01/E03记录不挪用。准备阶段模型和实际入口调用为0；原生全局计数未测量不写0。远端push仍受之前blocked by policy阻断，不重试绕行。
'''
    with (N/'execution-proposal.md').open('x',encoding='utf8',newline='\n') as f:f.write(proposal)
    report='''# 子进程准入最小补修：待独立准备审查

真实前例在clearance的Owned发现阶段失败。短暂PID的原生身份未落盘，其具体归属仍未证明。已确认的代码冲突是：actual child在领取clearance前调用admit→check_native_baseline→validate_protected_members→process_snapshot，后者生成PowerShell辅助进程，违背仅允许既定launcher/base的后代门。用实际admit调用链的受控OS观察回归获得RED：child-no-subprocess失败，其余16项通过；未改旧运行的根因结论。

最小补修只将native身份共同检查提取出来。check_native_baseline(child=True)用于actual/inert子端纯原生核验；父端默认完整核验及实际CLI前的完整核验不变。共享P4/P1、Owned、清理、原生模型transport、产品与入口均未改。authority、父时钟、源文件/模型哈希、证明时效、七成员精确绑定、clearance唯一消费均保留。

当前272项离线检查通过：原harness219（精确case ID与71函数保留）+新实际admit边界17+身份/transport边界10+入口26。首轮完整测试触及90秒，未产出JUnit/完成回执；只读进程快照确认当时无本例Python残留，该轮不计为RED或PASS。另一个新增fixture缺少scope.json造成17项setup失败，保留后补齐fixture。有效RED为1失败16通过，GREEN17通过。为保留原90秒离线上限，原测试按明确函数分为79与140两组，聚合case集合与旧219项完全一致，无跳过或遗漏。离线runner新增超时原始输出留存，实际275/310/315门不动。

原172/190包与实际失败/独审保持；1544输入绑定、9项无关工作区文件逐字核对。测试scratch仍保留本机；正式清单封存源码、快照、日志、JUnit、审计和回执，不以临时测试产物当真实交付。冷导入守卫及测试中的Python SSRF、稳定UUID4只用于离线，真实child未替换模型回答。

Review Focus：1 child是否仍能产生准入辅助进程；2父端parent/命令/CIM和七身份是否完整且在CLI前执行；3原生proof/authority/clock时效及唯一次clearance是否保留；4未知后代/PID复用/清理不确定是否仍失败关闭；5离线分组是否保留原全部case、原90秒上限和原实际时限。独审须逐项核对，不能用272项测试代替判断。

原短暂PID真实归属、真实8B事实质量、Rust DNS及实时清理只有后续单例能提供证据；准备没有这些信用。用户已授条件单例，审查PASS后直接执行，不重复询问。失败停止且保留所有原始记录。
'''
    with (N/'preparation-report.md').open('x',encoding='utf8',newline='\n') as f:f.write(report)
    members=set()
    for directory in ('harness','inputs','tests','verification','offline'):
        members.update(p for p in (N/directory).rglob('*') if p.is_file())
    members.update((N/'code'/name) for name in ('entry.py','bindings.py'))
    for run in (N/'code').glob('harness-preparation-*'):
        members.update(p for p in run.iterdir() if p.is_file() and p.name in {'receipt.json','stdout.log','stderr.log','source-before.json','source-after.json','offline-audit.json','root-timeout-record.json'})
        for directory in ('harness-source','harness'):
            members.update(p for p in (run/directory).glob('*') if p.is_file())
    members.update(N/name for name in ('plan.md','execution-proposal.md','preparation-report.md'))
    value=dict(kind='SOURCE13_REAL_CONTROLLED_PREPARATION',candidate='269aca511d88412dbb9c15d23911138469a37aa2',model='qwen3-8b-uncensored',
        model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',actual_released=False,
        test_count=272,prepared_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files={member_name(p):sha(p) for p in sorted(members)})
    save(N/'manifest.json',value)
    print(json.dumps(dict(manifest_sha256=sha(N/'manifest.json'),members=len(members),tests=272,actual_released=False)))

if __name__=='__main__':main()
