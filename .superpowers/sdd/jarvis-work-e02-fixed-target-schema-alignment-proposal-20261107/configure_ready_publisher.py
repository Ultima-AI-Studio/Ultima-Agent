from pathlib import Path
R=Path('H:/UltimaAI/UltimaAgent')
L=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
OL=R/'.superpowers/sdd/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107'
text=(OL/'publish_ready.py').read_text('utf8')
def rep(a,b):
    global text
    assert a in text,a
    text=text.replace(a,b)
for a,b in [('e02-native-write-diagnostics-20261107-r1','e02-fixed-target-schema-20261107-r1'),
 ('jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107','jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'),
 ('jarvis-e02-write-diagnostics','jarvis-e02-fixed-target-schema'),
 ('ultimaagent-t2-e02-write-diagnostics-ready-20261107','ultimaagent-t2-e02-fixed-target-ready-20261107'),
 ('181949cc71bcedca5c4604f63315b2bee92c2c86','40bb6cdd08c6e18a05d118165402e5965d00b90f'),
 ('e92ac27355d0633621ea41013942ce15a20693b7','4dc293524f372ae7811404bd03d213308734928f'),
 ('807','826'),('1549','1551'),('60来源','61来源'),
 ("=='6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696'","==load(N/'inputs/candidate-transition.json')['candidate']"),
 ('jarvis-work-t2-e02-write-diagnostics-preparation-20261107','jarvis-work-t2-e02-fixed-target-preparation-20261107'),
 ('有限写入诊断准备PASS','固定目标schema准备PASS'),
 ('SOURCE15_E02_WRITE_DIAGNOSTICS_REVIEWED_READY','SOURCE16_E02_FIXED_TARGET_SCHEMA_REVIEWED_READY'),
 (",goal_status='active'",''),
 ("(plan,'plans'),(report,'reports'),(correction,'reports'),","(plan,'plans'),(report,'reports'),"),
 ('e02-write-diagnostics-20261107-r1.md','e02-fixed-target-schema-20261107-r1.md'),
 ('src in (plan,correction)','src==plan'),
 ('report,plan,correction,order','report,plan,order'),
 ('seal reviewed writer diagnostics and one-case readiness','seal reviewed fixed-target schema and one-case readiness'),
 ('mirror writer diagnostics preparation and prior attribution correction','mirror fixed-target schema preparation')]:rep(a,b)
text='\n'.join(line for line in text.splitlines() if not line.startswith('correction='))+'\n'
rep("status='E02诊断候选6cb9284完成，826项离线检查/独立准备PASS；旧三次失败保留，已授权条件单例与结果复核，待一次当前8B原题四来源。E02/T2未过；旧E01/E03信用不转移。'", "status='E02固定目标schema候选'+entry.CANDIDATE[:7]+'准备完成，826项离线检查/独立准备PASS；全部旧失败保留，按已授权范围待一次当前8B原题四来源及结果复核。E02/T2未过；旧E01/E03信用不转移。'")
with (L/'publish_ready.py').open('x',encoding='utf8',newline='\n') as f:f.write(text)
print('Created readiness publisher only; not executed')
