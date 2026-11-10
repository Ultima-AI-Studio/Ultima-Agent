"""Additional readonly interpretation of already sealed service/CLI observations."""
from pathlib import Path
import hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');N=R/'data/evidence/jarvis-work-capability/T2/e02-code-claim-schema-20261107-r1';F=N/'actual/E02-controlled-1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
manifest=N/'review/result-inputs/result-manifest.json';m=load(manifest)
for name,digest in m['files'].items():assert sha(N/name)==digest,name
service=load(F/'service-first-result.json');cli=load(F/'product-result.json');failure=load(F/'trusted-export.failure.json')
artifacts=[]
for row in service['artifacts']:
    p=Path(row['path']);assert p.is_relative_to(F/'outputs') and sha(p)==row['sha256']
    artifacts.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p),service_verified=row.get('verified')))
attempts=service.get('research_attempts',[])
value=dict(kind='READONLY_SAVED_SERVICE_CLI_DISTINCTION',run_id=m['run_id'],candidate=load(N/'inputs/input-manifest.json')['candidate'],
    result_manifest_sha256=sha(manifest),cli_status=cli.get('status'),cli_error=cli.get('error'),
    cli_has_request_id='request_id' in cli,cli_has_session_id='session_id' in cli,
    service_status=service['status'],service_error=service.get('error'),service_request_id=service['request_id'],service_session_id=service['session_id'],
    service_task_id=service['task_id'],service_search_success=sum(r['tool_name']=='ultima_work_web_search' and r['success'] is True for r in attempts),
    service_GET_success=sum(r['tool_name']=='ultima_work_http_get' and r['success'] is True for r in attempts),
    service_available_sources=len(service['available_sources']),service_cited_sources=len(service['sources']),
    service_effect_states=[r['state'] for r in service.get('research_effects',[])],service_artifacts=artifacts,
    saved_export_failure_native_POST_attempts=failure['native_POST_attempts'],actual_native_start_count=failure['actual_native_start_count'],
    saved_export_failure_type=failure['error_type'],saved_export_complete=failure['complete'],saved_export_END=failure['END'],
    export_concrete_reason='UNKNOWN_NOT_SAVED',
    attribution='Observed submit saved service success before export_completed. Its ValueError handler saved failure then re-raised; outer HTTP handler returned500. Terminal request/session mismatch is a downstream observation of the identifier-free CLI error envelope. Exact export substage and rejected value remain unknown.',
    earlier_byte_readback_limit='search/GET/available zero and application native POST null were derived from the CLI error envelope, not proof that no work/model calls occurred. Preserve original readback and terminal unchanged.',
    source_files={str(p):sha(p) for p in [F/'service-first-result.json',F/'product-result.json',F/'trusted-export.failure.json',F/'terminal.json',N/'harness/adapter.py',Path(load(N/'inputs/input-manifest.json')['candidate_root'])/'src/brain/agent_server.py']},
    new_tests=0,new_product_calls=0,new_model_calls=0,new_network_requests=0,acceptance_credit=0,E02='NOT_PASSED',T2='NOT_PASSED')
out=N/'verification/service-result-readback.json'
with out.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(path=str(out),sha256=sha(out),service_status=service['status'],service_search=1,service_GET=4,export_native_POST=failure['native_POST_attempts'],credit=0)))
