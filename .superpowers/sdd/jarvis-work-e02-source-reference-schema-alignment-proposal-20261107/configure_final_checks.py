from pathlib import Path
import hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-fixed-target-schema-20261107-r1';N=T/'e02-source-reference-schema-20261107-r1'
OL=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
BASE='900b944165c0175b91492e3fe5b31d96aabdcd5c'
def new(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
def rep(text,old,value):
    assert old in text,old
    return text.replace(old,value)
text=(OL/'commit_product.py').read_text('utf8')
for old,value in [(OLD.name,N.name),('jarvis-e02-fixed-target-schema/UltimaAgent','jarvis-e02-source-reference/UltimaAgent'),
    ('ultimaagent-e02-fixed-target-candidate','ultimaagent-e02-source-reference-candidate'),
    ("[('target-green',19)","[('reference-green',29),('target-green',19)"),('total==537','total==566'),
    ('6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696',BASE),
    ('fix(research): align generation schema with fixed research target','fix(research): correlate visible source and evidence schema')]:text=rep(text,old,value)
start=text.index("changed=['src/brain/work_navigation.py'");end=text.index('record=checkpoint',start)
text=text[:start]+'''changed=['src/brain/agent_server.py','src/brain/work_navigation.py','src/brain/work_research.py','src/brain/tests/test_work_write_diagnostics.py','src/brain/tests/test_work_source_reference_schema.py']
assert set(gt(C,'diff','--name-only').splitlines())==set(changed[:-1])
assert gt(C,'ls-files','--others','--exclude-standard')==changed[-1]
'''+text[end:]
new(L/'commit_product.py',text)
text=(OL/'rebind_candidate.py').read_text('utf8')
text=text.replace('e02-fixed-target-schema-20261107-r1',N.name).replace('e02-native-write-diagnostics-20261107-r1',OLD.name)
text=text.replace('jarvis-e02-fixed-target-schema','jarvis-e02-source-reference').replace('jarvis-e02-write-diagnostics','jarvis-e02-fixed-target-schema')
text=text.replace('6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696',BASE)
text=text.replace('test_work_fixed_target_schema.py','test_work_source_reference_schema.py')
text=text.replace('Fixed research.md enum in v3 writer schema only; unchanged writer/END gates','Visible source/evidence schema in generation and independent replay; original writer/fact/END gates retained')
text=rep(text,"assert changed==['src\\\\brain\\\\work_navigation.py'],changed","assert set(changed)=={'src\\\\brain\\\\agent_server.py','src\\\\brain\\\\work_navigation.py','src\\\\brain\\\\work_research.py','src\\\\brain\\\\tests\\\\test_work_write_diagnostics.py'},changed")
new(L/'rebind_candidate.py',text)
p=N/'verification/run_binding_checks.py';text=p.read_text('utf8')
text=rep(text,"in ('red','green')","in ('red','red-bound','green')");p.write_text(text,encoding='utf8')
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nRuling: existing writer diagnostics now require valid incoming source/evidence pairs because malformed native envelopes are correctly rejected earlier. Preserve original diagnostic intent through test-only fault injection inside the real resolver boundary; duplicate-source fixture uses a correctly paired ref. Production responses are not rewritten. Cost if wrong: lost writer regression coverage; all17 original tests must still pass.\n')
    f.write('\nRuling: original Ollama PID5708 was replaced by already-running11464 while the other six identities, parent, executable, command hash, version0.32.15 and8B digest match. User denies active restart/update; app log shows app startup/oldPID cleanup but initiator is unknown. Preserve the old baseline and add a new exact seven-identity baseline for this candidate only, pinned by path and SHA. Read-only reconciliation is within continued identity verification; no service operation or model call. Cost if wrong: preflight refuses any identity drift, and no continuity credit is inferred. Independent preparation review must inspect this.\n')
    f.write('\nTask1: bindings-red16 had2 positive-control errors caused by incomplete candidate rebinding; the14 apparent passes are not valid RED proof. Keep that receipt; run a new red-bound stage after complete candidate rebinding and before exact new-baseline enforcement. Expected14pass/2fail, then GREEN16.\n')
plan=R/'docs/plans/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107.md'
with plan.open('a',encoding='utf8') as f:
    f.write('\n## 执行补充：保护身份只读核对\n\n本轮发现原Ollama PID5708已退出，现有PID11464由同一父进程24608启动，版本0.32.15、当前8B摘要、可执行文件和命令摘要相同，其余六个保护身份一致。用户call_bf5fa9f4197e4118b2aab2d505c6ae66答复没有主动关闭、重启或更新；应用日志记载启动与旧PID清理，启动来源仍未知。只读保存旧基线与新七身份基线，新基线仅用于本候选，必须固定路径及SHA并经准备独审；入口原native/CIM/parent/command/端口保护检查保持。没有服务操作、模型调用或连续存活断言。\n')
print('Created bounded commit/rebinding helpers and documented rulings; no runtime authority')
