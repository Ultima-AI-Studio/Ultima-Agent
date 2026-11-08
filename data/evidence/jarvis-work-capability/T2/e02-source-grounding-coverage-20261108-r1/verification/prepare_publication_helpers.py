"""Prepare scoped local publication tools before freezing their review manifest."""
from pathlib import Path
import ast,json
N=Path(__file__).resolve().parents[1];B=N.parent/'e02-claim-generation-contract-20261108-r1'
for name in ('closeout.py','publish.py','final_readback.py'):
    s=(B/'verification'/name).read_text('utf8')
    for a,b in {
        'claim-generation-contract':'source-grounding-coverage',
        'claim-generation-ready':'source-grounding-ready',
        'SOURCE34':'SOURCE36','source34':'source36','CLAIM_GENERATION':'SOURCE_GROUNDING',
        'call_5411de619a6c4de0bab414126a228c7d':'call_3d33440cc40c401ea7a2cf11c8bc2bcf',
        '1004':'1022',
        'c4caa739-c466-44f3-866b-0c57ea8c5e40':'1496a844-668d-407a-a91b-89be246ba05b',
        '6e30ba9b38ac11f49b88b908d9b8014a154cd9a4':'9ab8d0c6a064cd2bda557cf1f4e887e181ec9c57',
        '1cb79eef123f3bcf5e865457e9e801193b3761f6':'db6d02f8a787780b1d0a8a9d41eb9bf6e3b36ab1',
        'E02代码事实生成起点候选':'E02证据优先与未读来源机会候选',
        '保留尾部/引用/覆盖风险':'保留事实/引用/原题覆盖待验证风险',
        'seal operation-first offline preparation and review':'seal evidence-first and source-reserve preparation',
        'mirror claim generation offline preparation':'mirror source grounding offline preparation'
    }.items():s=s.replace(a,b)
    ast.parse(s)
    with (N/'verification'/name).open('x',encoding='utf8',newline='\n') as f:f.write(s)
print('publication and final readback tools prepared; not executed')
