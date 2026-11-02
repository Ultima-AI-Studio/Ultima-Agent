"""Ultima Agent 智能体服务器（常驻进程，venv-openjarvis 运行）。

三层架构中的"智能体服务器"层：薄壳（文字 CLI / 语音 daemon / 悬浮球壳）
通过本机 HTTP 接口调用本地 14B 主脑的自主对话循环（底座 OpenJarvis Agent 循环）。

接口：
- GET  /health   → 服务状态（模型 / agent / 已注册工具清单）
- POST /ask      → {"query": str, "max_tokens": int?} → {"content", "tool_results", "usage"}

设计约束：
- 仅标准库 + openjarvis + UltimaAgent 自有模块；
- 工具注册：import agent_tools_ultima 触发 ToolRegistry 装饰器注册；
- 模型：ollama + qwen2.5:14b（本地主脑）；agent：simple（ReAct 工具循环）。
"""

from __future__ import annotations

import json
import importlib
import importlib.util
import os
import queue
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

JARVIS_PERSONA_PATH = (
    PROJECT_ROOT
    / "libs"
    / "base"
    / "openjarvis"
    / "configs"
    / "openjarvis"
    / "prompts"
    / "personas"
    / "jarvis.md"
)
MAINBRAIN_RULES_PATH = PROJECT_ROOT / "docs" / "specs" / "mainbrain-rules-baseline.md"


def _read_required_prompt(path: Path, label: str) -> str:
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"{label} prompt source unavailable: {path}") from exc
    if not content:
        raise RuntimeError(f"{label} prompt source is empty: {path}")
    return content


def _load_mainbrain_system_prompt() -> str:
    """Load jarvis.md and the v1.0 authoritative rule block once at startup."""
    persona = _read_required_prompt(JARVIS_PERSONA_PATH, "Jarvis persona")
    baseline = _read_required_prompt(MAINBRAIN_RULES_PATH, "mainbrain rules")
    if "v1.0" not in baseline:
        raise RuntimeError("mainbrain rules baseline is not v1.0")
    block = re.search(r"```\s*\r?\n(.*?)\r?\n```", baseline, re.DOTALL)
    if block is None or not block.group(1).strip():
        raise RuntimeError("mainbrain rules baseline has no embeddable rule block")
    return f"{persona}\n\n{block.group(1).strip()}"


MAINBRAIN_SYSTEM_PROMPT = _load_mainbrain_system_prompt()

from openjarvis import Jarvis  # noqa: E402
from openjarvis.core.registry import ToolRegistry  # noqa: E402

try:  # 包导入用于测试；脚本入口走 fallback
    from .reply.schema import (  # type: ignore[attr-defined] # noqa: E402
        REPLY_JSON_SCHEMA,
        StructuredReply,
        StructuredReplyError,
        parse_structured_reply,
    )
except ImportError:  # pragma: no cover - 脚本入口
    from reply.schema import (  # type: ignore[no-redef] # noqa: E402
        REPLY_JSON_SCHEMA,
        StructuredReply,
        StructuredReplyError,
        parse_structured_reply,
    )


def _install_mainbrain_system_prompt() -> str:
    """Append the cached mainbrain block to native_react's real SYSTEM prompt."""
    from openjarvis.agents import native_react

    original_loader = native_react.load_system_prompt_override
    react_prompt = original_loader("native_react") or native_react.REACT_SYSTEM_PROMPT
    assembled = f"{react_prompt}\n\n{MAINBRAIN_SYSTEM_PROMPT}"

    def load_with_mainbrain(agent_name: str) -> str | None:
        if agent_name == "native_react":
            return assembled
        return original_loader(agent_name)

    native_react.load_system_prompt_override = load_with_mainbrain
    return assembled


NATIVE_REACT_SYSTEM_PROMPT = _install_mainbrain_system_prompt()

try:  # 包导入用于测试；脚本入口走 fallback
    from .events import get_event_bus  # type: ignore[attr-defined] # noqa: E402
except ImportError:  # pragma: no cover - 脚本入口
    from events import get_event_bus  # type: ignore[no-redef] # noqa: E402

HOST = "127.0.0.1"
PORT = 8756

ENGINE_KEY = "ollama"
MODEL = "qwen3-8b-uncensored"
AGENT = "native_react"
TOOLS = [
    "calculator",
    "think",
    "ultima_subagent",
    "ultima_skill_manage",
    "ultima_memory",
    "ultima_web_search",
    "ultima_task_query",
    "ultima_task_adjust",
    "ultima_env_snapshot",
]
DEFAULT_MAX_TOKENS = 1024
MAX_BODY_BYTES = 1024 * 1024  # 请求体上限 1MB（本地接口防异常大包）
SSE_PING_SECONDS = 15.0
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
STRUCTURED_REPLY_TIMEOUT_SECONDS = 180
STRUCTURED_FALLBACK_REPLY = "这个问题我暂时无法可靠回答。"
STRUCTURED_REPLY_SYSTEM_PROMPT = """\
你是本地 Agent 的最终回答边界。输出必须严格匹配给定 JSON Schema，禁止 markdown 和额外文本。
reply_text 最多两句，不含营销、关注、点赞或订阅话术。
confidence 是 0 到 1 的自评置信度。
grounded 仅当 reply_text 能被用户原文或工具证据直接支持时为 true；草稿本身不是证据。
无法确认时将 grounded 设为 false，并在 reply_text 中简短说明无法可靠回答。
"""


def _load_reply_style_once() -> tuple[tuple[str, ...], int]:
    try:
        from .voice.voice_profile import load_profile
    except ImportError:  # pragma: no cover - script entry
        from voice.voice_profile import load_profile

    style = load_profile()["style"]
    return tuple(style["banned_phrases"]), int(style["max_sentences"])


REPLY_BANNED_PHRASES, REPLY_MAX_SENTENCES = _load_reply_style_once()
EVENT_BUS = get_event_bus()

_jars: Jarvis | None = None
_ask_lock = threading.Lock()  # Jarvis 单例非线程安全，串行化并发推理
_manager_token: str | None = None
_work_service = None
_runtime_root: Path | None = None
_isolated = False


_RESEARCH_ORIGIN = 'http://127.0.0.1:11434'
_RESEARCH_DIGEST = '6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
_RESEARCH_MODEL = 'qwen3-8b-uncensored'


def _strict_json(data):
    def unique(pairs):
        result = dict(pairs)
        if len(result) != len(pairs):
            raise ValueError('Duplicate JSON field')
        return result
    value = json.loads(data, object_pairs_hook=unique)
    json.dumps(value, allow_nan=False)
    return value


def _research_output_tokens(value):
    if value is None:
        return 2048
    if type(value) is not int or value <= 0:
        raise ValueError('Research max_tokens must be a positive integer')
    return min(value,4096)


def _research_budget(messages, schema, output):
    from openjarvis.core.types import Message,Role
    from openjarvis.engine._base import estimate_prompt_tokens
    shape = json.dumps(schema,ensure_ascii=False,separators=(',',':'))
    if estimate_prompt_tokens([*messages,Message(role=Role.SYSTEM,content=shape)]) + 512 + output > 16384:
        raise ValueError('Research context estimate exceeds budget')


def _research_manifest_digest():
    import hashlib
    store = Path(os.environ.get('OLLAMA_MODELS') or Path.home()/'.ollama'/'models')
    manifest = store/'manifests'/'registry.ollama.ai'/'library'/_RESEARCH_MODEL/'latest'
    return hashlib.sha256(manifest.read_bytes()).hexdigest()


def _research_client():
    import httpx
    return httpx.Client(base_url=_RESEARCH_ORIGIN,trust_env=False,follow_redirects=False,timeout=25)


def _research_sampler_schema(schema):
    """Copy a JSON Schema, removing only sampler-incompatible length keywords."""
    from copy import deepcopy
    projected = deepcopy(schema)
    def visit(node):
        if not isinstance(node,dict):
            return
        node.pop('maxLength',None)
        for key in ('properties','patternProperties','definitions','$defs','dependentSchemas','dependencies'):
            for child in node.get(key,{}).values():
                visit(child)
        for key in ('additionalProperties','additionalItems','contains','propertyNames','not','if','then','else'):
            visit(node.get(key))
        for key in ('items','allOf','anyOf','oneOf'):
            children = node.get(key,[])
            for child in children if isinstance(children,list) else [children]:
                visit(child)
    visit(projected)
    return projected


def _research_message_dicts(messages):
    from dataclasses import asdict
    result=[]
    for message in messages:
        item=asdict(message); item['role']=message.role.value
        result.append(item)
    return result


class _ResearchTransport:
    """Request-local send reservations and bounded HTTPX application buffers."""
    def __init__(self,client,ledger):
        self.client=client; self.ledger=ledger
        self.generations=0; self.gets=0; self.posts=0; self.completed=0; self.post_bytes=0
        self.admitted={'metadata':0,'chat':0}
        self.receipts=[]

    def timeout(self,ack=False,*,now=None):
        from .work_tools import monotonic
        import httpx
        self.ledger._live()
        remaining=self.ledger.deadline-(monotonic() if now is None else now)
        if not ack:
            if remaining<=55: raise ValueError('Research author admission deadline')
            remaining-=55
        if remaining<=0: raise ValueError('Research acknowledgement deadline')
        base=min(25,remaining)
        return httpx.Timeout(base,read=min(25 if ack else 180,remaining))

    def check_return(self,ack):
        self.ledger._live()
        if ack: self.ledger.admit_ack()
        else: self.ledger.admit_report()

    def exchange(self,method,path,kind,*,entity=b'',ack=False):
        import hashlib
        if kind not in self.admitted: raise ValueError('Unknown research response domain')
        receipt=dict(method=method,path=path,kind=kind,entity_sha256=hashlib.sha256(entity).hexdigest(),
            entity_bytes=len(entity),downloaded=None,inspected=0,admitted=0,retained=0,peer_bytes=None,
            socket_bytes=None,error=None,send_reserved=False,admission_error=None,timeout_json=None)
        receipt_index=len(self.receipts); self.receipts.append(receipt)
        response=None; buffer=bytearray(); failure=None
        try:
            timeout=self.timeout(ack)
            if kind=='metadata': timeout.read=min(25,timeout.read)
            if method=='GET':
                if entity or self.gets>=16: raise ValueError('Metadata send cap')
            elif method=='POST':
                if self.posts>=8 or len(entity)>49152 or self.post_bytes+len(entity)>393216:
                    raise ValueError('Research POST entity cap')
            else: raise ValueError('Unsupported research method')
            prepared=self.client.build_request(method,path,content=entity,
                headers={'content-type':'application/json','accept-encoding':'identity'},timeout=timeout)
            if prepared.content!=entity or prepared.headers.get('content-encoding') or prepared.method!=method:
                raise ValueError('Prepared research entity drift')
            # Install the final admission-time timeout on this same entity.
            with self.ledger._lock:
                from .work_tools import monotonic
                admitted_at=monotonic()
                final_timeout=self.timeout(ack,now=admitted_at)
                if kind=='metadata': final_timeout.read=min(25,final_timeout.read)
                prepared.extensions['timeout']=final_timeout.as_dict()
                receipt['timeout_json']=json.dumps(prepared.extensions['timeout'],sort_keys=True,separators=(',',':'),allow_nan=False)
                if method=='GET': self.gets+=1
                else: self.posts+=1; self.post_bytes+=len(entity)
                receipt['send_reserved']=True
                self.ledger._mark('send',at=admitted_at,generation=self.generations,receipt_index=receipt_index)
            response=self.client.send(prepared,stream=True,follow_redirects=False)
            receipt['status']=response.status_code
            if response.status_code<200 or response.status_code>=300: raise ValueError('Research HTTP status')
            if response.headers.get('content-encoding','identity').lower()!='identity': raise ValueError('Research response encoding')
            cap=32768 if kind=='metadata' else 65536
            remaining=min(cap,524288-self.admitted[kind])
            length=response.headers.get('content-length')
            if length is not None and (not length.isascii() or not length.isdecimal() or int(length)>remaining):
                raise ValueError('Research Content-Length admission')
            for block in response.iter_raw(chunk_size=512):
                self.check_return(ack)
                remaining=min(cap-len(buffer),524288-self.admitted[kind])
                count=min(len(block),remaining)
                receipt['inspected']+=count
                buffer.extend(block[:count]); receipt['admitted']+=count; self.admitted[kind]+=count
                receipt['retained']=len(buffer)
                if len(block)>count:
                    receipt['inspected']+=1
                    raise ValueError('Research response overflow')
            self.check_return(ack)
            receipt['response_sha256']=hashlib.sha256(buffer).hexdigest()
            self.ledger._mark('return',generation=self.generations,receipt_index=receipt_index)
            if method=='POST': self.completed+=1
            return bytes(buffer)
        except Exception as exc:
            failure=exc; receipt['error']=type(exc).__name__
            if not receipt['send_reserved']:
                receipt['admission_error']=type(exc).__name__
                self.ledger._mark('admission_refused',generation=self.generations,receipt_index=receipt_index)
            raise
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception as exc:
                    if failure is None:
                        receipt['error']=type(exc).__name__
                        raise
                finally:
                    count=getattr(response,'num_bytes_downloaded',None)
                    receipt['downloaded']=count if type(count) is int and count>=0 else None


class _NativeResearchLeaf:
    engine_id = 'ollama'

    def __init__(self, client, ledger):
        self.client = client
        self.ledger = ledger
        self.transport = _ResearchTransport(client,ledger)
        self.expected = None
        self.raw_envelope = None
        self.wire_records = []

    def generate(self,messages,*,model,temperature,max_tokens,response_format):
        import hashlib
        from ollama import ChatResponse
        from ollama._types import ChatRequest
        from jsonschema import Draft7Validator
        from openjarvis.engine._base import messages_to_dicts,estimate_prompt_tokens
        from openjarvis.security.guardrails import GuardrailsEngine
        from .work_navigation import canonical_v3
        class NativeRequest(ChatRequest):
            truncate: bool = False
            shift: bool = False
        # The actual installed guard must call this leaf after its input scan;
        # matching unscanned messages alone do not establish that boundary.
        frame=sys._getframe(1)
        while frame is not None and frame.f_code is not GuardrailsEngine.generate.__code__:
            frame=frame.f_back
        if frame is None or frame.f_locals.get('self') is not self.guard:
            raise ValueError('Research guard boundary bypass')
        expected=self.expected
        if (expected is None or model!=_RESEARCH_MODEL or temperature!=0
                or _research_message_dicts(messages)!=expected['messages']
                or response_format!=expected['schema'] or max_tokens!=expected['limit']):
            raise ValueError('Secured research input drift')
        self.expected=None; self.raw_envelope=None
        _research_budget(messages,response_format,max_tokens)
        secured=messages_to_dicts(messages)
        self.ledger._scan_output([secured,response_format])
        if len(canonical_v3([secured,response_format]))>32768: raise ValueError('Research strict prompt byte cap')
        transport=self.transport
        if transport.generations>=8: raise ValueError('Research generation cap')
        transport.generations+=1
        self.ledger._mark('generation',generation=transport.generations)
        ack=expected['ack']
        from .work_research import checked_native_identity,checked_native_response
        version_bytes=transport.exchange('GET','/api/version','metadata',ack=ack)
        if _strict_json(version_bytes.decode('utf8'))!={'version':'0.32.15'}:
            raise ValueError('Unsupported native research version')
        tags_bytes=transport.exchange('GET','/api/tags','metadata',ack=ack)
        manifest_digest=_research_manifest_digest()
        version,tags=checked_native_identity(version_bytes,tags_bytes,manifest_digest)
        self.ledger._scan_output([version,tags])
        sampler=_research_sampler_schema(response_format)
        request=NativeRequest(model=model,messages=secured,format=sampler,tools=[],think=False,stream=False,
            options={'num_ctx':16384,'temperature':0,'num_predict':max_tokens})
        entity=canonical_v3(request.model_dump(exclude_none=True,mode='json'))
        raw_bytes=transport.exchange('POST','/api/chat','chat',entity=entity,ack=ack)
        raw=_strict_json(raw_bytes.decode('utf8'))
        message=raw.get('message'); counts=raw.get('prompt_eval_count'),raw.get('eval_count')
        checked_native_response(raw,max_tokens)
        self.ledger._scan_output(raw)
        typed=ChatResponse.model_validate(raw)
        envelope=_strict_json(message['content'])
        if not Draft7Validator(response_format).is_valid(envelope):
            raise ValueError('Invalid native research envelope')
        self.ledger._scan_output([raw,envelope])
        transport.check_return(ack)
        self.raw_envelope=envelope
        self.wire_records.append(dict(generation=transport.generations,secured_messages=secured,strict_schema=response_format,
            sampler_schema=sampler,entity=entity.decode('utf8'),raw_response=raw_bytes.decode('utf8'),raw=raw,raw_envelope=envelope,
            identity=dict(version_response=version_bytes.decode('utf8'),tags_response=tags_bytes.decode('utf8'),local_manifest_sha256=manifest_digest),
            hashes={k:hashlib.sha256(v).hexdigest() for k,v in dict(messages=canonical_v3(secured),
                strict=canonical_v3(response_format),sampler=canonical_v3(sampler),entity=entity).items()}))
        estimated=max(counts[0],estimate_prompt_tokens(messages))
        return dict(content=typed.message.content,model=typed.model,finish_reason=typed.done_reason,
            usage=dict(prompt_tokens=estimated,prompt_tokens_evaluated=counts[0],completion_tokens=counts[1],total_tokens=estimated+counts[1]))


def _checked_research_security(owner):
    from openjarvis.engine.ollama import OllamaEngine
    from openjarvis.security.guardrails import GuardrailsEngine
    from openjarvis.security.scanner import PIIScanner, SecretScanner
    from openjarvis.telemetry.instrumented_engine import InstrumentedEngine
    outer = owner._engine
    conf = owner.config.security
    if (type(outer) is not InstrumentedEngine or type(outer._inner) is not GuardrailsEngine
            or type(outer._inner._engine) is not OllamaEngine):
        raise ValueError('Unsupported structured research wrapper')
    guard = outer._inner
    raw = guard._engine
    scanners = [c for flag,c in ((conf.secret_scanner,SecretScanner),(conf.pii_scanner,PIIScanner)) if flag]
    if (raw._host not in (_RESEARCH_ORIGIN,'http://localhost:11434')
            or str(raw._client.base_url).rstrip('/') != raw._host or 'OLLAMA_API_KEY' in os.environ
            or not conf.enabled or not scanners or [type(s) for s in guard._scanners] != scanners
            or not (conf.scan_input and conf.scan_output and guard._scan_input and guard._scan_output)
            or guard._mode.value != conf.mode or outer._bus is not owner._bus or guard._bus is not owner._bus
            or owner._audit_logger is None or (conf.capabilities.enabled and owner._capability_policy is None)
            or (conf.rate_limit_enabled and owner._rate_limiter is None)):
        raise ValueError('Unsupported structured research origin, credentials or security')
    from .work_navigation import make_scan_policy
    return make_scan_policy(tuple(guard._scanners),conf.mode)


def _prepare_research_navigation(collection, *, binding, ledger):
    from .work_navigation import prepare_navigation,canonical_v3
    from copy import deepcopy
    with ledger.lock_for_report(_ask_lock):
        owner=get_jarvis()
        owner._ensure_engine()
        policy=_checked_research_security(owner)
        records=canonical_v3([r for r in ledger.snapshot() if r.get('tool_name')=='ultima_work_http_get'])
        catalogue=prepare_navigation(collection,binding,policy,get_records_json=records,deadline=ledger.deadline)
        ledger._prepare_navigation(binding,catalogue,collection,records,policy)
        ledger._security_identity=(owner._engine,owner._engine._inner,owner._engine._inner._engine,
            owner._engine._inner._engine._client,owner.config.security,owner._audit_logger,owner._capability_policy,owner._rate_limiter)
        ledger._security_config=deepcopy(owner.config.security)
        return catalogue


def _borrow_research(owner, binding, ledger, caps, prompt):
    from copy import copy
    policy=_checked_research_security(owner)
    ledger._check_policy(policy)
    current=(owner._engine,owner._engine._inner,owner._engine._inner._engine,
        owner._engine._inner._engine._client,owner.config.security,owner._audit_logger,owner._capability_policy,owner._rate_limiter)
    if any(a is not b for a,b in zip(current,ledger._security_identity)) or owner.config.security!=ledger._security_config:
        raise ValueError('Research wrapper identity drift')
    outer=owner._engine
    guard=outer._inner
    borrowed = copy(outer)
    borrowed._inner = copy(guard)
    view = _ResearchEngineView(borrowed,binding,ledger,caps,prompt)
    client = _research_client()
    borrowed._inner._engine = _NativeResearchLeaf(client,ledger)
    view.leaf = borrowed._inner._engine
    view.leaf.guard=borrowed._inner
    ledger._runtime_wires=view.leaf.wire_records
    ledger._runtime_transport=view.leaf.transport
    ledger._runtime_prompt=prompt
    return view,client


class _ResearchEngineView:
    """Validate the complete SDK conversation around the existing guard stack."""
    def __init__(self, inner, binding, ledger, caps, prompt):
        self.prompt=prompt; self.caps=caps; self.inner=inner
        self.binding=binding; self.ledger=ledger
        self.expected=None; self.final=False; self.history=None; self.last_content=None
        self.leaf=None; self.generation=0

    def __getattr__(self,name): return getattr(self.inner,name)

    def observe(self,event):
        if event.event_type.value.startswith('tool_'):
            self.ledger.observe_navigation(event,caller_id=self.ledger._caller,binding_key=self.caps.navigation.binding_key)

    def check_dispatch(self,observation=''):
        self.ledger._live()
        if self.expected and (self.ledger._expected is None or not self.ledger._expected['ended']):
            self.ledger.seal('Unconfirmed research tool dispatch')
            raise ValueError(self.ledger.first_failure)

    def _system(self):
        import hashlib
        from openjarvis.agents import native_react
        from openjarvis.tools._stubs import build_tool_descriptions
        from openjarvis.tools.description_loader import get_tool_description_override
        template=native_react.REACT_SYSTEM_PROMPT
        if hashlib.sha256(template.encode()).hexdigest()!='a062f71243cd4986a2f2034cf3946912196fd4f4499394815cb0d3a1c522579b':
            raise ValueError('Unknown research template')
        startup=template+'\n\n'+MAINBRAIN_SYSTEM_PROMPT
        if NATIVE_REACT_SYSTEM_PROMPT!=startup or native_react.load_system_prompt_override('native_react')!=startup:
            raise ValueError('Conflicting research template override')
        if native_react.load_few_shot_exemplars('native_react'):
            raise ValueError('Research exemplars are not authorized')
        if any(get_tool_description_override(name) for name in ('ultima_work_research_inspect','ultima_work_research_write')):
            raise ValueError('Research tool description override is not authorized')
        tools=[self.ledger._enrolled[k] for k in ('ultima_work_research_inspect','ultima_work_research_write')]
        system=startup.format(skill_examples='',tool_descriptions=build_tool_descriptions(tools))
        prefix=template.split('# Using Skills',1)[0]
        if hashlib.sha256(prefix.encode()).hexdigest()!='f1ac2c27009f1759da22b3dfc6f301d0912ba8370f1dd3964433421910474621' or system.count(prefix)!=1:
            raise ValueError('Research format prefix drift')
        replacement=('Return exactly one JSON object matching the phase schema. Use action and object action_input '
            'for one permitted SDK tool, or final_answer for refusal or the authorized final acknowledgement. '
            'Write prose style applies inside user-facing text only.\n\n')
        return system,system.replace(prefix,replacement,1)

    def _verify_file(self):
        from .work_research import verify_research_artifacts
        from .work_verifier import verify_artifacts
        records,effects=self.ledger.outcome_snapshot()
        reports=[r for r in records if r['tool_name']=='ultima_work_research_write' and r.get('success')]
        writes=[r for r in records if r['tool_name']=='ultima_work_file_write' and r.get('success')]
        if (len(effects)!=1 or len(reports)!=1 or len(writes)!=1 or effects[0]['state']!='completed'
                or effects[0].get('file_call_id')!=writes[0]['call_id']
                or effects[0].get('report_call_id')!=reports[0]['call_id']):
            raise ValueError('Unlinked research write')
        verify_research_artifacts(self.binding,verify_artifacts(self.binding,writes),reports,self.caps.research_json,
            required_version=3,issued_snapshot=self.ledger.issued_snapshot,runtime_packet=self.ledger._runtime_packet(),runtime_inputs=self.ledger._runtime_inputs)
        self.ledger.admit_ack()

    def generate(self,messages,**kwargs):
        from dataclasses import replace
        import copy,hashlib
        from jsonschema import Draft7Validator
        from openjarvis.core.types import Message,Role
        from .work_navigation import canonical_v3,v3_writer_schema
        self.check_dispatch()
        self.generation+=1
        if self.final: raise ValueError('Research already finalized')
        if self.history is None:
            self.ledger.close_enrollment()
            original,replaced=self._system()
            self.original_system=original; self.replaced_system=replaced
            self.ledger._runtime_system=original
            self.history=_research_message_dicts([Message(role=Role.SYSTEM,content=original),Message(role=Role.USER,content=self.prompt)])
        else:
            staged=self.ledger._staged.get(self.ledger._sequence)
            if not staged or not staged['confirmed']: raise ValueError('Missing confirmed observation')
            self.history+=_research_message_dicts([Message(role=Role.ASSISTANT,content=self.last_content),
                Message(role=Role.USER,content='Observation: '+staged['content'])])
        if _research_message_dicts(messages)!=self.history: raise ValueError('Research SDK history drift')
        final=dict(type='object',additionalProperties=False,required=['final_answer'],
            properties=dict(final_answer=dict(type='string',minLength=1,maxLength=1000)))
        ack=self.expected=='ultima_work_research_write'
        pending=self.ledger._staged.get(self.ledger._sequence)
        reads=list(self.ledger._issued)
        if pending and pending.get('view') and pending['confirmed'] and not pending['promoted']:
            reads.append((pending['key'],pending['view']))
        eligible=len({view.source_id for _,view in reads if json.loads(view.cards_json)})>=3
        alternatives=[]
        def action(name,params):
            return dict(type='object',additionalProperties=False,required=['action','action_input'],
                properties=dict(action=dict(enum=[name]),action_input=params))
        if ack:
            self._verify_file(); schema=final; limit=min(kwargs['max_tokens'],256)
            phase='Acknowledge the verified research.md file. No further action is authorized.'
        else:
            self.ledger.admit_report()
            if self.ledger._read_count<6:
                alternatives.append(action('ultima_work_research_inspect',self.ledger._enrolled['ultima_work_research_inspect'].spec.parameters))
            if eligible: alternatives.append(action('ultima_work_research_write',v3_writer_schema()))
            schema=dict(anyOf=[*alternatives,final])
            limit=min(kwargs['max_tokens'],2048 if eligible else 256)
            phase=('Inspect safe source pages; author only atomic claims supported by the exact returned witnesses. '
                'Use at least three distinct source URLs and bodies. Write only research.md once, or refuse with final_answer. '
                'The phase schema is the entire output contract. Full argument schema (JSON):\n'
                +json.dumps(v3_writer_schema(),ensure_ascii=False,separators=(',',':'))+'\nEnd argument schema.')
        outgoing=[replace(messages[0],content=self.replaced_system+'\n\n'+phase),*messages[1:]]
        _research_budget(outgoing,schema,limit)
        self.leaf.expected=dict(messages=copy.deepcopy(_research_message_dicts(outgoing)),schema=copy.deepcopy(schema),limit=limit,ack=ack)
        result=self.inner.generate(outgoing,model=kwargs['model'],temperature=0,max_tokens=limit,response_format=schema)
        value=_strict_json(result['content'])
        if not Draft7Validator(schema).is_valid(value): raise ValueError('Invalid secured research envelope')
        self.ledger._scan_output([result['content'],value])
        if self.leaf.raw_envelope is None or value!=self.leaf.raw_envelope:
            raise ValueError('Secured research output drift')
        self.leaf.transport.check_return(ack)
        self.leaf.wire_records[-1]['secured_envelope']=value
        self.ledger._mark('secured',generation=self.generation)
        if pending and pending.get('view') and not pending['promoted']:
            self.ledger.promote_visible(pending['key'].generation,pending['view'].wire_sha256)
        self.last_content=result['content']
        if 'final_answer' in value:
            if not value['final_answer'].strip(): raise ValueError('Empty research final answer')
            self.final=True; self.expected=None
            if ack: self.ledger._runtime_final=self.ledger._runtime_packet()
        else:
            self.ledger.admit_report()
            self.expected=value['action']
            self.ledger.expect(self.ledger._sequence+1,self.expected,hashlib.sha256(canonical_v3(value['action_input'])).hexdigest())
        return result


def _run_work_agent(query, *, binding, tools, max_tokens=None):
    from openjarvis.core.events import EventType
    from .work_tools import _ACTIVE
    from copy import copy
    bound = _ACTIVE.get()
    research = bool(bound and bound[0] is binding and bound[2] and bound[2].research_json)
    allowance = _research_output_tokens(max_tokens) if research else (max_tokens or 2048)
    with bound[1].lock_for_report(_ask_lock) if research else _ask_lock:
        jars = get_jarvis()
        view = client = None
        if research:
            jars._ensure_engine()
            if (jars._resolved_engine_key != 'ollama' or AGENT != 'native_react'
                    or jars._model_override != 'qwen3-8b-uncensored'):
                raise ValueError('Unsupported structured research engine, agent or model')
            if jars.config.agent.max_turns < 8:
                raise ValueError('Research requires room for six reads, write and ACK')
            jars = copy(jars)
            view,client = _borrow_research(jars,binding,bound[1],bound[2],query)
            jars._engine = view
        trace = []
        caller = threading.get_ident()
        def collect(event):
            if threading.get_ident() != caller or _ACTIVE.get() is not bound:
                return
            trace.append(dict(type=event.event_type.value, timestamp=event.timestamp, data=event.data))
            if view and event.event_type != EventType.INFERENCE_END:
                view.observe(event)
        kinds = (EventType.INFERENCE_END, EventType.TOOL_CALL_START, EventType.TOOL_CALL_END)
        if view:
            kinds += (EventType.TOOL_TIMEOUT, EventType.INFERENCE_START,)
        for kind in kinds:
            jars._bus.subscribe(kind, collect)
        result = {}
        try:
            if view: bound[1].open_enrollment(binding,caller)
            result = jars.ask_full(query, agent=AGENT, tools=tools, context=False,
                                   max_tokens=allowance)
            if view:
                view.check_dispatch()
                if not view.final:
                    result['compose_error'] = 'Research stopped without a final envelope'
            result['trace'] = trace
            return result
        except Exception as exc:
            if not view:
                raise
            result.update(compose_error=str(exc), trace=trace)
            return result
        finally:
            if view:
                with bound[1]._lock:
                    if view.final and not result.get('compose_error') and not bound[1].first_failure:
                        bound[1]._sealed=True
                        bound[1]._permit=None
                    else: bound[1].seal(result.get('compose_error') or 'Research conversation closed')
            if client is not None:
                try:
                    client.close()
                except Exception as exc:
                    bound[1]._close_errors=getattr(bound[1],'_close_errors',[])+[type(exc).__name__]
                    reason=result.get('compose_error') or 'Research owned client close failed'
                    bound[1].seal(reason)
                    result['compose_error']=reason
            for kind in kinds:
                jars._bus.unsubscribe(kind, collect)



def _hardware_summary() -> str:
    """Return a compact, dependency-free hardware summary for the HUD tick."""
    memory_gb = 0
    try:
        import ctypes

        class _MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = _MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            memory_gb = round(status.total_physical / (1024**3))
    except (AttributeError, OSError):
        pass
    memory = f" · {memory_gb}GB" if memory_gb else ""
    return f"{os.cpu_count() or 0}C{memory}"


def _network_totals() -> tuple[int, int]:
    """Read Windows interface byte totals without adding a runtime dependency."""
    try:
        completed = subprocess.run(
            ["netstat", "-e"],
            capture_output=True,
            text=True,
            encoding="mbcs",
            errors="ignore",
            timeout=2,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for line in (completed.stdout or "").splitlines():
            values = re.findall(r"\d+", line)
            if len(values) == 2 and max(map(int, values)) > 1024:
                return int(values[0]), int(values[1])
    except (OSError, subprocess.SubprocessError):
        pass
    return 0, 0


def _read_manager_token() -> str:
    global _manager_token
    if _manager_token is not None:
        return _manager_token
    security_path = PROJECT_ROOT.parent / "UltimaManager" / "src" / "manager" / "security.py"
    spec = importlib.util.spec_from_file_location("ultima_manager_security", security_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Manager credential module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _manager_token = str(module.CredentialStore().read())
    return _manager_token


def _manager_active_tasks() -> list[dict[str, str]]:
    """Read the authenticated Manager task view; never expose its capability."""
    request = Request(
        "http://127.0.0.1:18766/api/v1/tasks?project_id=UltimaAgent",
        headers={"Authorization": "Bearer " + _read_manager_token()},
    )
    with urlopen(request, timeout=3) as response:
        payload = json.load(response)
    active_states = {"executing", "in_progress", "running", "develop", "plan", "plan_review", "audit"}
    tasks: list[dict[str, str]] = []
    for item in payload.get("items", []):
        state = str(item.get("state", "")).lower()
        if state in active_states:
            tasks.append(
                {
                    "work_order_id": str(item.get("work_order_id", "")),
                    "title": str(item.get("title", ""))[:120],
                    "state": state,
                }
            )
    for item in payload.get("legacy", []):
        state = str(item.get("registry_state", "")).lower()
        if state in active_states:
            tasks.append(
                {
                    "work_order_id": str(item.get("work_order_id", "")),
                    "title": str(item.get("registry_detail", ""))[:120],
                    "state": state,
                }
            )
    return tasks


def _hud_tick_loop() -> None:
    """Publish sticky system/Manager fields consumed by the eight-anchor HUD."""
    previous_rx, previous_tx = _network_totals()
    previous_time = time.monotonic()
    manager_tasks: list[dict[str, str]] = []
    manager_ok = False
    next_manager_read = 0.0
    tick = 0
    while True:
        tick += 1
        now = time.monotonic()
        rx, tx = _network_totals()
        elapsed = max(now - previous_time, 0.001)
        down_bps = max(0, round((rx - previous_rx) / elapsed)) if previous_rx else 0
        up_bps = max(0, round((tx - previous_tx) / elapsed)) if previous_tx else 0
        previous_rx, previous_tx, previous_time = rx, tx, now
        if now >= next_manager_read:
            try:
                manager_tasks = _manager_active_tasks()
                manager_ok = True
            except (HTTPError, URLError, OSError, RuntimeError, ValueError):
                manager_tasks = []
                manager_ok = False
            next_manager_read = now + 10.0
        EVENT_BUS.set_sticky(
            "tick",
            {
                "tick": tick,
                "hardware": _hardware_summary(),
                "connection": "Agent + Manager" if manager_ok else "Agent online",
                "down_bps": down_bps,
                "up_bps": up_bps,
                "manager_ok": manager_ok,
                "manager_tasks": manager_tasks,
                "queue_count": len(manager_tasks),
            },
        )
        time.sleep(2.0)


def _ensure_tools_registered() -> None:
    """只加载一次工具注册模块，并兼容脚本/包两种模块身份。"""
    if "agent_tools_ultima" in sys.modules:
        return
    package_name = f"{__package__}.agent_tools_ultima" if __package__ else ""
    if package_name and package_name in sys.modules:
        sys.modules["agent_tools_ultima"] = sys.modules[package_name]
        return
    module = importlib.import_module(".agent_tools_ultima", __package__) if __package__ else importlib.import_module("agent_tools_ultima")
    sys.modules.setdefault("agent_tools_ultima", module)


# ---------------------------------------------------------------------------
# RU-05 启动自检接线（工单⑧ T2）：主链路启动后后台静默查更新。
# N6 静默降级：通道异常/无网络只记日志，不打扰、不误报新版；N7 零弹窗。
# ---------------------------------------------------------------------------
def _startup_update_check() -> None:
    """后台线程：启动自检（best-effort，任何异常只记日志，不阻断主链路）。"""
    try:
        from src.update.triggers import UpdateTriggerEngine
        from src.update.channel import UpdateChannel

        repo = "Ultima-AI-Studio/Ultima-Agent"
        current = "0.1.0"  # 与宿主壳 csproj Version 对齐（当前发布基线）
        state_file = PROJECT_ROOT / ".runtime" / "update-state.json"
        channel = UpdateChannel(repo)
        engine = UpdateTriggerEngine(
            channel,
            current_version_provider=lambda: current,
            target_path=PROJECT_ROOT / "dist",
            state_file=state_file,
        )
        engine.startup_check()
    except Exception as exc:  # noqa: BLE001 - 静默降级（N6），不阻断启动
        sys.stderr.write(f"[agent-server] startup update check skipped (silent): {exc}\n")


def get_jarvis() -> Jarvis:
    global _jars
    if _jars is None:
        _ensure_tools_registered()
        if _isolated:
            from openjarvis.core.config import JarvisConfig
            config = JarvisConfig()
            config.telemetry.enabled = False
            config.analytics.enabled = False
            config.agent.context_from_memory = False
            # Relocate all dataclass path settings, including lazily opened stores.
            from dataclasses import fields, is_dataclass
            def relocate(obj, prefix='sdk'):
                for field in fields(obj):
                    value = getattr(obj, field.name)
                    if is_dataclass(value):
                        relocate(value, prefix + '-' + field.name)
                    elif isinstance(value, str) and ('path' in field.name or field.name.endswith('_dir')):
                        setattr(obj, field.name, str(_runtime_root / (prefix + '-' + field.name)))
            relocate(config)
            config._config_dir = _runtime_root
            _jars = Jarvis(config=config, engine_key=ENGINE_KEY, model=MODEL)
        else:
            _jars = Jarvis(engine_key=ENGINE_KEY, model=MODEL)
    return _jars


def _clean_content(content: str) -> str:
    """清理 ReAct 响应文本：只保留 Final Answer 之后的内容；无标记则原样返回。"""
    if not content:
        return content
    marker = "Final Answer:"
    if marker in content:
        return content.split(marker, 1)[1].strip()
    return content.strip()


def _structured_evidence(tool_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for item in tool_results:
        evidence.append(
            {
                "tool_name": str(item.get("tool_name", "tool")),
                "success": bool(item.get("success")),
                "content": str(item.get("content", ""))[:4000],
            }
        )
    return evidence


def _request_structured_reply(
    query: str,
    draft: str,
    tool_results: list[dict[str, Any]],
    *,
    retry_note: str | None = None,
) -> StructuredReply:
    """Render the exposed answer through Ollama's native JSON Schema grammar."""
    user_payload = json.dumps(
        {
            "user_query": query,
            "agent_draft": draft,
            "tool_evidence": _structured_evidence(tool_results),
            "retry_note": retry_note,
        },
        ensure_ascii=False,
    )
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": STRUCTURED_REPLY_SYSTEM_PROMPT},
            {"role": "user", "content": user_payload},
        ],
        "stream": False,
        "think": False,
        "format": REPLY_JSON_SCHEMA,
    }
    request = Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=STRUCTURED_REPLY_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body.get("message", {}).get("content", "")
        if not isinstance(content, str):
            raise StructuredReplyError("Ollama message content must be a string")
        return parse_structured_reply(content)
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StructuredReplyError(f"structured Ollama request failed: {type(exc).__name__}") from exc


def _fallback_verifier():
    try:
        from .routing.reply_verifier import get_reply_verifier
    except ImportError:  # pragma: no cover - script entry
        from routing.reply_verifier import get_reply_verifier

    return get_reply_verifier(REPLY_BANNED_PHRASES, REPLY_MAX_SENTENCES)


def _structured_verifier():
    try:
        from .routing.reply_verifier import get_reply_verifier
    except ImportError:  # pragma: no cover - script entry
        from routing.reply_verifier import get_reply_verifier

    return get_reply_verifier(
        REPLY_BANNED_PHRASES,
        REPLY_MAX_SENTENCES,
        enforce_grounded=True,
        enforce_confidence=True,
    )


def _verified_reply(reply: StructuredReply):
    try:
        from .routing.reply_verifier import ReplySchema
    except ImportError:  # pragma: no cover - script entry
        from routing.reply_verifier import ReplySchema

    return _structured_verifier().verify(
        ReplySchema(
            reply_text=reply.reply_text,
            confidence=reply.confidence,
            grounded=reply.grounded,
        )
    )


def _fixed_structured_fallback() -> StructuredReply:
    return StructuredReply(STRUCTURED_FALLBACK_REPLY, 1.0, True)


def _constrain_reply(
    query: str,
    draft: str,
    tool_results: list[dict[str, Any]],
) -> tuple[StructuredReply, bool]:
    """Enforce structure, grounding and confidence with at most one retry."""
    try:
        candidate = _request_structured_reply(query, draft, tool_results)
    except StructuredReplyError:
        try:
            from .routing.reply_verifier import ReplySchema
        except ImportError:  # pragma: no cover - script entry
            from routing.reply_verifier import ReplySchema

        checked = _fallback_verifier().verify(ReplySchema(reply_text=draft))
        if checked.accepted and checked.text:
            # A sanitized draft still lacks trustworthy generated metadata.
            _verified_reply(StructuredReply(checked.text, 0.0, False))
        return _fixed_structured_fallback(), True

    checked = _verified_reply(candidate)
    if checked.accepted:
        return StructuredReply(checked.text, candidate.confidence, candidate.grounded), False
    if "confidence_below_threshold" in checked.issues or "confidence_required" in checked.issues:
        return _fixed_structured_fallback(), True
    if "grounded_required" in checked.issues:
        try:
            retried = _request_structured_reply(
                query,
                draft,
                tool_results,
                retry_note=(
                    "上一回答 grounded=false，未通过真实性门。只重答这一次；"
                    "仅在用户原文或工具证据直接支持时 grounded=true，否则明确无法可靠回答。"
                ),
            )
        except StructuredReplyError:
            return _fixed_structured_fallback(), True
        retry_checked = _verified_reply(retried)
        if retry_checked.accepted:
            return StructuredReply(
                retry_checked.text,
                retried.confidence,
                retried.grounded,
            ), False
    return _fixed_structured_fallback(), True


def ask_once(query: str, max_tokens: int | None = None) -> dict[str, Any]:
    """执行一轮自主对话：本地 14B 自主决定直接回答或调用工具（并发串行化）。

    全程向事件总线发布真实事件（四角壳 HUD 消费）：
    - 收到提问 → message_in（w-agent 流：用户消息）
    - 开始回复 → stream_start（w-agent 流：回复中）
    - 工具调用 → tool_executing / tool_call（w-hb 流）
    - 完成回复 → message（w-msg 流：AI 气泡）
    """
    EVENT_BUS.emit_event("message_in", {"text": query, "role": "user"})
    j = get_jarvis()
    with _ask_lock:
        EVENT_BUS.emit_event("stream_start", {"text": "Ultima 正在回复…"})
        # 注入当前时间作为 grounded 事实：8B 无时间工具，不注入则"现在几点/今天几号"只能兜底
        import datetime as _dt

        _now = _dt.datetime.now()
        _weekdays = "一二三四五六日"
        _time_ctx = "[当前时间：{0:%Y-%m-%d} {0:%H:%M} 星期{1}（北京时间）]".format(
            _now, _weekdays[_now.weekday()]
        )
        query_with_ctx = f"{_time_ctx} {query}"
        result = j.ask_full(
            query_with_ctx,
            agent=AGENT,
            tools=TOOLS,
            context=False,
            max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
        )
    draft = _clean_content(result.get("content", ""))
    tool_results = result.get("tool_results", [])
    structured_reply, degraded = _constrain_reply(query_with_ctx, draft, tool_results)
    content = structured_reply.reply_text
    for tr in tool_results:
        EVENT_BUS.emit_event(
            "tool_executing",
            {"tool": tr.get("tool_name", "tool"), "name": tr.get("tool_name", "tool")},
        )
        EVENT_BUS.emit_event(
            "tool_call",
            {
                "tool": tr.get("tool_name", "tool"),
                "name": tr.get("tool_name", "tool"),
                "text": (tr.get("content") or "")[:200],
                "ok": bool(tr.get("success")),
            },
        )
    EVENT_BUS.emit_event("message", {"text": content, "role": "jarvis"})
    return {
        "content": content,
        "reply_text": structured_reply.reply_text,
        "confidence": structured_reply.confidence,
        "grounded": structured_reply.grounded,
        "structured_reply": structured_reply.to_dict(),
        "structured_degraded": degraded,
        "tool_results": tool_results,
        "usage": result.get("usage", {}),
    }


class _Handler(BaseHTTPRequestHandler):
    server_version = "UltimaAgentServer/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[agent-server] {fmt % args}\n")

    def _send_json(self, status: int, payload: Any) -> None:
        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError) as exc:  # 载荷不可序列化：返回可读 500
            body = json.dumps(
                {"ok": False, "error": f"响应序列化失败：{exc}"}, ensure_ascii=False
            ).encode("utf-8")
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _write_sse(self, event_type: str, payload: dict[str, Any], event_id: str = "") -> None:
        lines = []
        if event_id:
            lines.append(f"id: {event_id}")
        lines.append(f"event: {event_type}")
        lines.append(
            "data: "
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        )
        self.wfile.write(("\n".join(lines) + "\n\n").encode("utf-8"))
        self.wfile.flush()

    def _serve_events(self, query: dict[str, list[str]]) -> None:
        client_id = (query.get("client_id") or [""])[0] or "anonymous"
        last_event_id = (query.get("last_event_id") or [""])[0]
        if not last_event_id:
            last_event_id = self.headers.get("Last-Event-ID", "")

        pending: queue.Queue[dict[str, Any]] = queue.Queue()
        unsubscribe = EVENT_BUS.subscribe(pending.put)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            history = EVENT_BUS.history()
            latest_event_id = history[-1]["id"] if history else ""
            connected = {
                "type": "connected",
                "data": {
                    "client_id": client_id,
                    "service_time": time.time(),
                    "resumed_from_event_id": last_event_id,
                    "latest_event_id": latest_event_id,
                },
                "ts": time.time(),
            }
            self._write_sse("connected", connected)

            sent_ids: set[str] = set()
            for event in EVENT_BUS.get_sticky().values():
                self._write_sse(event["type"], event, event["id"])
                sent_ids.add(event["id"])

            replay = EVENT_BUS.get_after(last_event_id) if last_event_id else history
            for event in replay:
                if event["id"] in sent_ids:
                    continue
                self._write_sse(event["type"], event, event["id"])
                sent_ids.add(event["id"])

            while True:
                try:
                    event = pending.get(timeout=SSE_PING_SECONDS)
                except queue.Empty:
                    ping = {
                        "type": "ping",
                        "data": {"service_time": time.time()},
                        "ts": time.time(),
                    }
                    self._write_sse("ping", ping)
                    continue
                if event["id"] in sent_ids:
                    continue
                self._write_sse(event["type"], event, event["id"])
                sent_ids.add(event["id"])
        except (BrokenPipeError, ConnectionResetError, OSError):
            return
        finally:
            unsubscribe()

    def _serve_event_history(self, query: dict[str, list[str]]) -> None:
        path = (query.get("path") or ["all"])[0].lower()
        try:
            requested_limit = int((query.get("limit") or ["240"])[0])
            if requested_limit < 0:
                raise ValueError
            payload = EVENT_BUS.history(path=path, limit=min(requested_limit, 240))
        except ValueError:
            self._send_json(400, {"ok": False, "error": "path 或 limit 参数无效。"})
            return
        self._send_json(200, payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if route == "/health":
            # 返回 14B 实际可调用的工具白名单，而非全部注册工具
            self._send_json(200, {"ok": True, "model": MODEL, "agent": AGENT, "tools": TOOLS})
            return
        if route == "/events":
            self._serve_events(query)
            return
        if route == "/events/history":
            self._serve_event_history(query)
            return
        self._send_json(404, {"ok": False, "error": "未找到该路径。"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/ask":
            self._send_json(404, {"ok": False, "error": "未找到该路径。"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self._send_json(413, {"ok": False, "error": "请求体过大。"})
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
            query = str(payload.get("query", "")).strip()
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"ok": False, "error": "请求体不是合法 JSON。"})
            return
        if not query:
            self._send_json(400, {"ok": False, "error": "query 不能为空。"})
            return
        try:
            max_tokens = payload.get("max_tokens")
            context = payload.get('context')
            if payload.get('mode')=='work' and isinstance(context,dict) and context.get('research') is True:
                max_tokens = _research_output_tokens(max_tokens)
            elif max_tokens is not None:
                max_tokens = int(max_tokens)  # 非数字 → 400 参数错误（不误报推理失败）
        except (TypeError, ValueError):
            self._send_json(400, {"ok": False, "error": "max_tokens 必须为整数。"})
            return
        try:
            if payload.get('mode') == 'work':
                if _work_service is None:
                    result = dict(request_id=payload.get('request_id'), session_id=payload.get('session_id'), task_id=None, status='failed', content='', artifacts=[], tool_results=[], error='Work output root is not configured')
                elif set(payload) - {'mode', 'query', 'request_id', 'session_id', 'context', 'max_tokens'}:
                    result = dict(request_id=payload.get('request_id'), session_id=payload.get('session_id'), task_id=None, status='failed', error='Unknown work request or authority fields', artifacts=[], content='', tool_results=[])
                else:
                    result = _work_service.submit_work(query, request_id=payload.get('request_id'), session_id=payload.get('session_id'), context=payload.get('context'), max_tokens=max_tokens)
            elif payload.get('mode') not in (None, 'chat'):
                self._send_json(400, {'ok': False, 'error': 'Unsupported mode'})
                return
            else:
                result = ask_once(query, max_tokens=max_tokens)
            result["ok"] = True
            self._send_json(200, result)
        except Exception as exc:  # 推理异常返回可读错误
            self._send_json(500, {"ok": False, "error": f"推理失败：{exc}"})


def main(argv=None) -> int:
    import argparse
    global PORT, _runtime_root, _isolated, _work_service
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--runtime-root', type=Path)
    parser.add_argument('--work-output-root', type=Path)
    parser.add_argument('--work-target-policy', type=Path)
    parser.add_argument('--work-research', action='store_true')
    parser.add_argument('--isolated', action='store_true')
    args = parser.parse_args(argv)
    PORT = args.port
    _isolated = args.isolated
    _runtime_root = args.runtime_root.resolve() if args.runtime_root else None
    if _isolated and (_runtime_root is None or args.work_output_root is None):
        parser.error('--isolated requires --runtime-root and --work-output-root')
    if _runtime_root:
        _runtime_root.mkdir(parents=True, exist_ok=True)
    if args.work_output_root:
        from src.brain.work_service import WorkService
        provider=None
        browser=None
        if args.work_target_policy:
            from src.brain.work_context import WorkContextProvider
            provider=WorkContextProvider(json.loads(args.work_target_policy.read_text(encoding='utf-8-sig')))
        if args.work_research:
            from src.brain.browser.channel import BrowserChannel
            browser=BrowserChannel()
        _work_service = WorkService(args.work_output_root, runner=_run_work_agent, context_provider=provider, browser_channel=browser, research_preparer=_prepare_research_navigation)
    # 单实例守卫（2026-10-27 性能修复）：ThreadingHTTPServer 默认
    # allow_reuse_address=True，双实例可同时 bind 同一端口 → 每次测试
    # 拉一个新实例且不回收，进程累积吃满机器。先探测端口/再查 pid 锁。
    try:
        import urllib.request as _urlreq

        with _urlreq.urlopen(f"http://{HOST}:{PORT}/health", timeout=1) as _resp:
            sys.stderr.write("[agent-server] 已有实例在运行（health 有响应），本实例退出。\n")
            return 0
    except Exception:
        pass  # 端口无响应：继续，尝试自己接管

    import ctypes
    import tempfile

    _lock = (_runtime_root / "agent-server.pid") if _isolated else Path(tempfile.gettempdir()) / "ultima-agent-server.pid"

    def _holder_alive() -> bool:
        try:
            old = int(_lock.read_text().strip())
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, old)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
        except Exception:
            pass
        return False

    if _holder_alive():
        sys.stderr.write("[agent-server] 已有实例在运行（pid 锁存活），本实例退出。\n")
        return 0
    try:
        _lock.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    import atexit

    def _cleanup_lock() -> None:
        try:
            if _lock.read_text().strip() == str(os.getpid()):
                _lock.unlink(missing_ok=True)
        except Exception:
            pass

    atexit.register(_cleanup_lock)

    # 端口独占（Windows SO_EXCLUSIVEADDRUSE）：禁 SO_REUSEADDR 双 bind，
    # 极端竞态下两个实例同时启动时，后到者 bind 失败自动退出，杜绝双实例并存。
    import socket as _sock_mod

    _sock = _sock_mod.socket(_sock_mod.AF_INET, _sock_mod.SOCK_STREAM)
    _sock.setsockopt(_sock_mod.SOL_SOCKET, _sock_mod.SO_EXCLUSIVEADDRUSE, 1)
    try:
        _sock.bind((HOST, PORT))
    except OSError:
        sys.stderr.write(f"[agent-server] 端口 {PORT} 已被占用（已有实例在运行），本实例退出。\n")
        return 0
    _sock.listen(128)
    server = ThreadingHTTPServer((HOST, PORT), _Handler, bind_and_activate=False)
    server.socket = _sock
    sys.stderr.write(
        f"[agent-server] 启动：http://{HOST}:{PORT} model={MODEL} agent={AGENT} tools={TOOLS}\n"
    )
    if not _isolated:
        threading.Thread(target=_hud_tick_loop, daemon=True).start()
    # RU-05 启动自检：后台静默线程，失败不阻断主链路（N6/N7）
    if not _isolated:
        threading.Thread(target=_startup_update_check, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("[agent-server] 收到终止信号，退出。\n")
    finally:
        server.server_close()
        if _jars is not None:
            _jars.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
