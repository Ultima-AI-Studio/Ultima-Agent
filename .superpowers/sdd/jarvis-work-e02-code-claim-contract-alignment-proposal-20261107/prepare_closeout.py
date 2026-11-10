"""Prepare result publication helpers only; do not run them before review."""
from pathlib import Path
import re
R=Path('H:/UltimaAI/UltimaAgent')
OL=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107';L=Path(__file__).parent
changes={'e02-source-reference-schema-20261107-r1':'e02-code-claim-schema-20261107-r1',OL.name:L.name,
    'call_33506a697ec545c6b2a396ff83086672':'call_99e734b15417466b92af3e8e85fdc3ea',
    'ultimaagent-t2-e02-source-reference-result-':'ultimaagent-t2-e02-code-claim-result-',
    'jarvis-work-t2-e02-source-reference-result-20261107.md':'jarvis-work-t2-e02-code-claim-result-20261107.md',
    'jarvis-work-t2-e02-source-reference-preparation-20261107.md':'jarvis-work-t2-e02-code-claim-preparation-20261107.md',
    'SOURCE17_E02_SOURCE_REFERENCE_REVIEWED_RESULT':'SOURCE18_E02_CODE_CLAIM_REVIEWED_RESULT',
    '来源与证据schema对齐':'代码事实契约对齐','E02来源证据候选':'E02代码事实候选','来源证据schema单例':'代码事实契约单例',
    '857':'888','产品566':'产品594及官方转换3',
    'chore(e02): preserve reviewed source-reference single-case result':'chore(e02): preserve reviewed code-claim single-case result',
    'docs(e02): mirror source-reference single-case result':'docs(e02): mirror code-claim single-case result'}
def swap(text):return re.sub('|'.join(re.escape(k) for k in changes),lambda m:changes[m[0]],text)
text=swap((OL/'publish_result.py').read_text('utf8'))
start=text.index("候选{b['candidate']}，基于900b944。")
end=text.index('\n\n最终888',start)
text=text[:start]+'''候选{b['candidate']}，基于冻结a0d21eb。可信可见卡片按source/evidence/operation生成精确代码事实约束，generation和独立runtime replay重建相同schema/phase；不提前promotion、不改写模型回答。原research.md、事实/代码证据/重复来源、END/ACK/两次读回与时限门保留。新增28项产品回归，另3项使用官方b10488参考转换器核对兼容性；参考转换不代替实际原生采样证明。准备详情见jarvis-work-t2-e02-code-claim-preparation-20261107.md。'''+text[end:]
start=text.index('本例前只读记录现有Ollama11464')
end=text.index('\n\n原cleanup=',start)
text=text[:start]+'''本例直接复用上一候选已独审的七身份基线，固定路径和SHA不变。本轮准备及实际前后只读核验现有身份；Ollama11464在上一轮已替代5708，启动来源仍未知，不归因于用户或本轮，也未进行服务控制。'''+text[end:]
start=text.index('本轮执行裁决：')
end=text.index('\n\n远端push',start)
text=text[:start]+'''本轮执行裁决：保留旧候选、工作区和证据（代价为存储）；用官方支持的分组/字符类/分支表达原operation边界，既有事实门保持（长输入可能仍被原预算拒绝，不扩限）；离线准备不计真实研究信用；全局原生计数、持续存活、OS全流量及E02/T2总体验收保持未测量或未通过。初始RED、官方格式断言失败与离线命令拼写错误均保留，不计最终通过数。'''+text[end:]
for name,content in [('publish_result.py',text),('final_result_readback.py',swap((OL/'final_result_readback.py').read_text('utf8')))]:
    with (L/name).open('x',encoding='utf8',newline='\n') as f:f.write(content)
print('Prepared conditional result publication; no actual or result review invoked')
