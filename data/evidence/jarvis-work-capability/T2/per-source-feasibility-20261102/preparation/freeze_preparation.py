"""Offline packaging only. No socket, model, SDK owner or execution authority."""
from pathlib import Path
import difflib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
import run_stage_prefix as h


def main():
    h.socket_guard(mock=True)
    sys.path.insert(0,str(h.CHECKOUT))
    source21=h.strict((h.ROOT/'native-read-budget-source9/source-current.json').read_text(encoding='utf8'))
    frozen5=h.strict((h.ROOT/'native-read-budget-source9/frozen-inputs.json').read_text(encoding='utf8'))
    actual={name:h.sha((h.CHECKOUT/name).read_bytes()) for name in source21}
    assert actual==source21
    assert all(actual[name]==digest for name,digest in frozen5.items())
    assert h.sha(h.DESIGN.read_bytes())=='b1290ae6633418b9ab04a2b88ff9152655a8b30cbde79d795d8f3c18321d17d7'
    query,catalogue=h.load_material()
    scripts=[h.PREP/name for name in ('run_stage_prefix.py','test_stage_prefix.py','freeze_preparation.py')]
    compile_receipt=[]
    for path in scripts:
        compile(path.read_text(encoding='utf8'),str(path),'exec')
        compile_receipt.append(dict(path=str(path),sha256=h.sha(path.read_bytes()),compiled=True))
    h.save(h.PREP/'compile.json',compile_receipt)
    (h.PREP/'prompt.txt').write_text(h.PROMPT,encoding='utf8')
    templates=[]
    for source in catalogue:
        view,omitted=h.project(source)
        table=h.cards(source,view)
        schema=h.schema_for('00000000-0000-0000-0000-000000000000',table)
        name=source['source_id']+'-template.json'
        h.save(h.PREP/name,dict(original_query=query,source=source,view=view,omitted_ranges=omitted,table=table,schema=schema))
        templates.append(h.PREP/name)
    h.save(h.PREP/'schema-template.json',h.schema_for('00000000-0000-0000-0000-000000000000',{i:None for i in range(1,49)}))
    h.save(h.PREP/'preservation.json',dict(source21=actual,frozen5=frozen5,all_match=True,
        unchanged_product_test_count=293,tests_rerun=False,old_evidence_read_only=True,
        current_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=h.CHECKOUT,text=True).strip()))
    h.save(h.PREP/'scope.json',dict(authorized_write_root=str(h.PREP),
        authorized_report=str(h.CHECKOUT/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/task-2-per-source-probe-report.md'),
        product_source21_unchanged=True,frozen5_unchanged=True,actual_runroot_created=False,
        sdk_modified=False,actual_network_requests=0,actual_native_posts=0,
        git_status=subprocess.check_output(['git','status','--short'],cwd=h.CHECKOUT,text=True)))
    h.save(h.PREP/'argv.json',dict(executable='H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe',
        argv=['-B','-X','utf8','-m','pytest',str(h.PREP/'test_stage_prefix.py'),'-q','-p','no:cacheprovider',
              '--basetemp',str(h.PREP/'pytest-frozen-final'),'--junitxml',str(h.PREP/'tests-frozen-final.xml')],
        env=dict(TEMP=str(h.PREP/'temp'),TMP=str(h.PREP/'temp'),TMPDIR=str(h.PREP/'temp'),
                 OPENJARVIS_HOME=str(h.PREP/'sdk-home'),HF_HOME=str(h.PREP/'cache'),
                 XDG_CACHE_HOME=str(h.PREP/'cache'),
                 HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')))
    xml=ET.parse(h.PREP/'tests-frozen-final.xml').getroot()
    suite=next(iter(xml)) if xml.tag=='testsuites' else xml
    test_summary=dict(suite.attrib)
    assert int(test_summary['failures'])==int(test_summary['errors'])==0
    frozen_files={str(h.CHECKOUT/name):digest for name,digest in source21.items()}
    for path in [*scripts,*templates,h.PREP/'prompt.txt',h.PREP/'schema-template.json',h.DESIGN]:
        frozen_files[str(path)]=h.sha(path.read_bytes())
    manifest=dict(status='READY_FOR_INDEPENDENT_HARNESS_REVIEW',head=h.HEAD,
        purpose='evidence-only SDK source prefix; no actual inference executed',
        frozen_files=frozen_files,input_files={str(p):h.sha(p.read_bytes()) for p in (h.CORPUS,h.FREEZE,h.ARCHIVE)},
        review_path=str(h.ROOT/'per-source-design-review-2/verdict.json'),
        review_sha256=h.sha((h.ROOT/'per-source-design-review-2/verdict.json').read_bytes()),
        budget=dict(A=2048,N=4,k=5,num_predict=480,num_ctx=16384,max_native_posts=1,max_trial_metadata_gets=2,
                    separate_bootstrap_health_gets=1,total_deadline=260,reserve=55,max_stage_slice=36),
        model=h.MODEL,digest=h.DIGEST,daemon_version='0.32.15',test_summary=test_summary,
        actual_execution_released=False,actual_post_count=0,
        first_authority_source='S2',actual_runroot_parent=str(h.ROOT/'per-source-feasibility-20261102/S2-first'),
        authority_fields=dict(mode='single_source_sdk_prefix',execute=True,source_id='S2',head=h.HEAD,
                              max_native_posts=1,run_root='ROOT MUST SELECT A NEW EXCLUSIVE PATH',
                              manifest_sha256='ROOT MUST HASH THIS MANIFEST AFTER REVIEW'),
        material_limits=['MockTransport scripted stage is mechanical proof only, never factual acceptance.',
                         'Standalone lock is the actual imported server lock in this process, not cross-process contention proof.',
                         'S2 first actual result must receive independent sentence-by-sentence fact review; no retries.',
                         'No total multi-source deadline, bundle, writer, delivery or E02 acceptance established.'])
    h.save(h.PREP/'manifest.json',manifest)
    text=[]
    for path in scripts:
        text.extend(difflib.unified_diff([],path.read_text(encoding='utf8').splitlines(True),
                                        fromfile='/dev/null',tofile=str(path)))
    (h.PREP/'new-helper-package.diff').write_text(''.join(text),encoding='utf8')
    print(json.dumps(dict(status=manifest['status'],manifest_sha256=h.sha((h.PREP/'manifest.json').read_bytes()),
        script_sha256=h.sha(scripts[0].read_bytes()),test_summary=test_summary),indent=2))


if __name__=='__main__': main()
