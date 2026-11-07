from pathlib import Path
R=Path('H:/UltimaAI/UltimaAgent')
L=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
OL=R/'.superpowers/sdd/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107'
text=(OL/'final_result_readback.py').read_text('utf8')
def rep(a,b):
    global text
    assert a in text,a
    text=text.replace(a,b)
rep('e02-native-write-diagnostics-20261107-r1','e02-fixed-target-schema-20261107-r1')
rep("assert review['verdict']==registration['independent_review']=='FAIL_CONFIRMED'", "assert review['verdict']==registration['independent_review']\nassert review['verdict'] in ('PASS_CONTROLLED_CASE','FAIL_CONFIRMED')\naccepted=review['verdict']=='PASS_CONTROLLED_CASE'")
rep("registration['current_controlled_passed']==0 and registration['acceptance_credit'] is False", "registration['current_controlled_passed']==int(accepted) and registration['acceptance_credit'] is accepted")
rep("'PASS_REVIEWED_FAILURE_PUBLICATION_ONLY'", "'PASS_REVIEWED_SINGLE_CASE_PUBLICATION_ONLY'")
rep("independent_result='FAIL_CONFIRMED'", "independent_result=review['verdict']")
rep('research_credit=0','research_credit=int(accepted)')
with (L/'final_result_readback.py').open('x',encoding='utf8',newline='\n') as f:f.write(text)
print('Created final result verifier only')
