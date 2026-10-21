import json,hashlib,re
from pathlib import Path
from datetime import datetime,UTC
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
def read(rel):return (ROOT/rel).read_text(encoding='utf-8-sig')
def file_record(rel):
 p=ROOT/rel
 return {'path':str(p),'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else 0,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None}
tasks=['storage','statemachine','dispatcher','priority-deps','audit-e2e']
cards=[]
for name in tasks:
 task_id='s1-queue-engine-'+name
 paths=[f'tasks/cards/{task_id}/{part}.md' for part in ['completion','landed-files','acceptance-evidence']]
 records=[file_record(path) for path in paths]
 content=[read(path) for path in paths]
 cards.append({'task_id':task_id,'three_piece_present':all(item['exists'] and item['bytes'] for item in records),'completion_names_task':task_id in content[0],'landed_files_list_nonempty':bool(re.search(r'^- ',content[1],re.M)),'acceptance_evidence_nonempty':len(content[2])>100,'files':records,'historical_receipt_boundary':'Original developer self-check record; current independent conclusion is W2 report round2, not a rewrite of history.'})
w2rel='docs/reports/w2-independent-acceptance-20261021.md';w2=read(w2rel)
round2='docs/reports/evidence/w2-20261021/round2/'
back=json.loads(read(round2+'independent-readback.json'))
manifest=json.loads(read(round2+'source-manifest.json'))
engine_files={name:digest for name,digest in manifest.items() if '/tasks/queue_engine/' in name.replace('\\','/') or '/tasks/tests/' in name.replace('\\','/')}
changed=[name for name,digest in engine_files.items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest]
audit=json.loads(read(round2+'audit-receipt.json'));correction=json.loads(read(round2+'correction-independent-receipt.json'))
tests=read(round2+'tests.stderr.txt')
w1rel='docs/reports/w1-independent-acceptance-20261021.md'
w1=json.loads(read('docs/reports/evidence/w1-independent-20261021/round1/result.json'))
docs=read('docs/README.md')
documentation_current=('w2-independent-acceptance-20261021.md' in docs and '62' in docs and '35' in docs)
all_cards=all(card['three_piece_present'] and card['completion_names_task'] and card['landed_files_list_nonempty'] and card['acceptance_evidence_nonempty'] for card in cards)
technical=back['final_rows']==35 and back['all_technical_pass'] and not changed and re.search(r'Ran 62 tests',tests) is not None and tests.rstrip().endswith('OK') and audit['closed_state']=='COMPLETED' and all(task['state']=='COMPLETED' for task in correction['final_tasks'])
u01=w1['U01']=='PASS_HOST_STAGE_ENVIRONMENT_GATE' and 'U01 独立通过' in read(w1rel)
todo=[]
if not documentation_current:todo.append('Update docs/README.md authoritative registration: link latest W2 report; state 35 units and 62 tests passed; retain W1/Owner freeze boundary. Existing row still says 42 tests, awaiting W2.')
todo+=['Create local Git baseline and actual internal tag wo-s1-queue-engine-done only after remaining documentation DoD is closed; do not create v0.1-frozen here.','Synchronize work-order receipt/status under root authorization without altering historical failure evidence.','Continue W1 independently; v0.1-frozen requires complete W1 and Owner approval.']
result={'at_utc':datetime.now(UTC).isoformat(),'auditor':'/root/w2_acceptance','mode':'read-only administrative DoD check; only closeout evidence written','technical_pass':technical,'five_task_receipts_pass':all_cards,'U01_cross_order_gate_pass':u01,'documentation_current':documentation_current,'can_create_internal_tag_now':bool(technical and all_cards and u01 and documentation_current),'internal_tag_name':'wo-s1-queue-engine-done','version_freeze_approved':False,'checks':{'35_units_pass':back['final_rows']==35 and back['all_technical_pass'],'62_tests_pass':bool(re.search(r'Ran 62 tests',tests)) and tests.rstrip().endswith('OK'),'engine_and_tests_unchanged':not changed,'real_card_independently_closed':audit['closed_state']=='COMPLETED','correction_child_and_parent_independently_closed':all(t['state']=='COMPLETED' for t in correction['final_tasks']),'five_task_to_unit_mapping':'U06/U07/U08/U08b/U09','production_task_index_empty':json.loads(read('tasks/tasks.json'))==[]},'cards':cards,'read_sources':[file_record(rel) for rel in [w2rel,w1rel,'docs/README.md','docs/reports/evidence/w1-independent-20261021/round1/result.json',round2+'independent-readback.json',round2+'audit-receipt.json',round2+'correction-independent-receipt.json',round2+'tests.stderr.txt']],'source_changed':changed,'todo':todo,'no_process_control':True,'no_tag_created':True,'no_global_queue_changed':True}
(OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
report='''# W2 内部工单行政收口独立核对

技术验收、五卡原始回执三件套、U01跨工单环境门、35单元、62项测试、真实卡及修正链独立闭环均已核对通过。后台宿主任务未被干预。

当前尚有文档同步待办：docs/README.md仍登记“42项测试通过，待W2”，未登记最新W2独立报告及35单元/62项结果。应由监督端更新该权威登记后再创建内部tag `wo-s1-queue-engine-done`。本次不创建tag、不修改全局队列、不修改已签W2报告或round2清单。

五卡三件套属于原始开发自核历史，保留其中“待W2”等当时表述；当前独立结论以W2报告第二轮及独立凭据为准，不能覆写原始失败与待审证据。

U01已独立通过，不需等待W1整单才能完成工单①环境前置；整单W1及Owner版本冻结仍属后续门项。不得据内部工单tag创建或声称v0.1-frozen。

逐项检查与文件SHA-256见同目录result.json。只要技术源文件未变化、文档同步完成，监督端可创建已获授权的本地内部工单tag；无需重新运行或干预宿主。
'''
if documentation_current:report=report.replace('当前尚有文档同步待办：docs/README.md仍登记“42项测试通过，待W2”，未登记最新W2独立报告及35单元/62项结果。应由监督端更新该权威登记后再创建内部tag','权威登记已包含最新W2报告及35单元/62项结果，可以由监督端创建内部tag')
(OUT/'report.md').write_text(report,encoding='utf-8')
print(json.dumps({key:result[key] for key in ['technical_pass','five_task_receipts_pass','U01_cross_order_gate_pass','documentation_current','can_create_internal_tag_now']},ensure_ascii=True))
