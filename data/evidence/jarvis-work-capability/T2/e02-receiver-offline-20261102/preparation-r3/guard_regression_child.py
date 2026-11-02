"""Inert control: literal-extract ONLY authored guards, never import the probe."""
from pathlib import Path
import ast
import json
import os
import sys
import time

runner, output, mode = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
source = runner.read_text(encoding='utf8')
tree = ast.parse(source)
guards = '\n\n'.join(ast.get_source_segment(source,n) for n in tree.body
                       if isinstance(n,ast.FunctionDef) and n.name in ('prohibit','deadline'))
scope = dict(OUT=output, ENTRY=time.monotonic(), PROHIBITED_ATTEMPTS=[],
             os=os, json=json, time=time)
exec(compile(guards, '<authored-guard-literal>', 'exec'), scope)
dummy = {'__name__':'openjarvis.tools.inert_fixture'}
exec('def execute():\n    raise AssertionError("dummy body must never run")\n', dummy)
sys.settrace(scope['deadline'])
try:
    if mode == 'denial':
        dummy['execute']()
    else:
        raise ValueError('ordinary compatibility rejection')
except Exception as exc:
    # Exact class of recovery shape found in compat; old trace PermissionError
    # reaches here and disables tracing. New denial must end the interpreter.
    sys.settrace(None)
    record = dict(caught=type(exc).__name__, error=str(exc), trace_now=sys.gettrace() is not None,
                  first_attempts=scope['PROHIBITED_ATTEMPTS'])
    (output/'caught.json').write_text(json.dumps(record),encoding='utf8')
    (output/'continuation-sentinel.txt').write_text('post-denial recovery resumed',encoding='utf8')
    print(json.dumps(record))
    if mode == 'denial':
        raise SystemExit(17)  # expected RED: prevention oracle failed
    raise SystemExit(0)
finally:
    sys.settrace(None)
raise SystemExit(18)
