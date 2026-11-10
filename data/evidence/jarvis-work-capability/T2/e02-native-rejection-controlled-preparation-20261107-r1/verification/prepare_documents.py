"""Prepare the exact proposal and post-review local closeout, never a live grant."""
from pathlib import Path
N=Path(__file__).resolve().parents[1];OLD=N.parent/'e02-json-string-controlled-preparation-20261107-r1'
HEAD='d860b2ab4e4d9974e33c96472e4ea15abb807280'
def write(p,s):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(s)
def replace(s,a,b):
    assert a in s,a;return s.replace(a,b)
def common(s):
    return s.replace('6d758d9c3961f156a062e349ec4a949e2ee7a9a9',HEAD).replace('6d758d9','d860b2a').replace('jarvis-e02-json-string-projection','jarvis-e02-native-rejection').replace('json-string-controlled','native-rejection-controlled')
s=common((OLD/'execution-proposal.md').read_text('utf8'))
s=replace(s,'HTTP失败时保留当前产品v3私有诊断：代次、固定路由、真实HTTP状态、请求实体SHA/字节数、send_reserved和有界接收计数。500正文不读取；200后坏JSON/schema/扫描失败保持状态200但不标validated。私有回执须经过原adapter导出、绑定和摘要核验；不能从模型文本或旧日志补造状态。',
    '当前产品输出v4私有失败诊断。保留原last_http回执；仅原生外层校验拒绝时新增固定原因、受限计数、请求/响应SHA及字节数，绑定同一generation与receipt。500正文不读取；坏JSON/schema/扫描失败不得冒充原生拒绝。私有回执经原adapter观察器导出，写后ACK拒绝保留已写入事实；诊断不等于完整runtime、END或交付。')
s=replace(s,'上一 N15 的 5e6ea89c-8e47-43a6-9480-7a11d72cabf5 失败与 N16 的 781 项离线通过均不迁移成当前实际信用。原生二进制和真实 8B 对新投影的行为尚未实际验证。',
    '上一N17的bc216374-f59c-4967-99f2-ded53a4ea49d仍为FAIL_CONFIRMED：HTTP200后原生响应校验拒绝，无research.md，具体拒绝谓词未保存。N18的909项离线准备不转为实际信用。本例旨在保留确切拒绝条件，同时仍按原题完整交付要求验收，不以诊断成功替代任务成功。')
write(N/'execution-proposal.md',s)
s=common((OLD/'verification/closeout.py').read_text('utf8'))
s=s.replace('344','346').replace('SOURCE27_E02_JSON_STRING_CONTROLLED','SOURCE29_E02_NATIVE_REJECTION_CONTROLLED').replace('source27_preparation','source29_preparation').replace('e02_json_string_controlled_preparation','e02_native_rejection_controlled_preparation')
start=s.index('text=f"""');end=s.index('for p in (report_path',start)
s=s[:start]+'''text=(N/'preparation-report.md').read_text('utf8').replace('状态：待独立准备审查。','状态：PASS_OFFLINE_AND_INDEPENDENT_PREPARATION_REVIEW；仅准备通过。',1)
text+='\\n独立准备审查PASS_PREPARATION_ONLY；manifest '+MANIFEST+'，'+str(member_count)+'成员；review SHA256 '+sha(review_path)+'。harness-approval/read_ready通过，缺少grant时read_release拒绝，run_once未调用。\\n'
'''+s[end:]
s=replace(s,"R/'.superpowers/sdd/jarvis-work-e02-native-rejection-controlled-entry-plan-20261107/progress.md'","N/'progress.md'")
s=s.replace('61 entry/binding/boundary + 283 deduplicated adapter; N16 product781 frozen baseline not rerun','61 entry/binding/boundary + 285 deduplicated adapter; N18 product909 frozen baseline not rerun')
s=s.replace('C14 frozen','C15 frozen').replace('JSON string controlled preparation complete','native rejection controlled preparation complete')
write(N/'verification/closeout.py',s)
s=common((OLD/'verification/publish.py').read_text('utf8'))
s=replace(s,"R/'.superpowers/sdd/jarvis-work-e02-native-rejection-controlled-entry-plan-20261107/progress.md'","N/'progress.md'")
s=s.replace('a9f24dd4985c2270a84c763af4e7371dd7991350','5972719db54af4fae8ea2cb52ee70d5a0d846d0e').replace('d913cec262316d8c0ddc6998ac21c3097484dd88','4d7017937db66625e55b9c8ea9828c554deb593b')
s=s.replace('JSON-string candidate','native rejection candidate').replace('JSON-string controlled entry','native rejection controlled entry').replace('foreign_files_unchanged=9',"foreign_files_unchanged=len(json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'])")
write(N/'verification/publish.py',s)
print('Prepared concrete proposal, LF closeout and exact local publication; no actual allocation')
