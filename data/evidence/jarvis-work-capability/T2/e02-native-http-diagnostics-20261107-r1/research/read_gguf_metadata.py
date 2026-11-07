"""Read bounded GGUF metadata, never tensors or inference, using the pinned header layout."""
from pathlib import Path
import datetime as dt,hashlib,json,struct
N=Path(__file__).resolve().parents[1];D=N/'research/model'
manifest=Path('C:/Users/Administrator/.ollama/models/manifests/registry.ollama.ai/library/qwen3-8b-uncensored/latest')
raw=manifest.read_bytes();assert hashlib.sha256(raw).hexdigest()=='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
config=json.loads(raw);layers=config['layers'];assert len(layers)==1 and layers[0]['mediaType']=='application/vnd.ollama.image.model'
p=Path('C:/Users/Administrator/.ollama/models/blobs')/layers[0]['digest'].replace(':','-')
before=p.stat();assert before.st_size==layers[0]['size'];CAP=16*1024*1024
fmt={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
values={};keys=[]
with p.open('rb') as f:
    def read(n):
        assert 0<=n<=CAP and f.tell()+n<=CAP
        b=f.read(n);assert len(b)==n;return b
    def unpack(code):return struct.unpack('<'+code,read(struct.calcsize('<'+code)))[0]
    def string(keep=True):
        size=unpack('Q');assert size<=CAP
        if keep:return read(size).decode('utf8')
        assert f.tell()+size<=CAP;f.seek(size,1)
    def value(kind,keep=False):
        if kind in fmt:
            v=unpack(fmt[kind]);return v if keep else None
        if kind==8:return string(keep)
        assert kind==9
        item=unpack('I');count=unpack('Q');assert item!=9 and count<=1000000
        if item in fmt:
            size=struct.calcsize('<'+fmt[item])*count;assert f.tell()+size<=CAP;f.seek(size,1)
        else:
            assert item==8
            for _ in range(count):string(False)
        return dict(item_type=item,count=count) if keep else None
    assert read(4)==b'GGUF';version=unpack('I');assert version==3
    tensors=unpack('Q');pairs=unpack('Q');assert 0<pairs<10000
    for _ in range(pairs):
        key=string();assert key not in keys;keys.append(key);kind=unpack('I')
        keep=key in ('general.architecture','general.name','tokenizer.chat_template','tokenizer.ggml.bos_token_id','tokenizer.ggml.eos_token_id')
        v=value(kind,keep)
        if keep:values[key]=v
    end=f.tell();f.seek(0);prefix=read(end)
after=p.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
template=values['tokenizer.chat_template'];assert type(template) is str and 0<len(template.encode())<=65536
with (D/'chat-template.jinja').open('x',encoding='utf8',newline='') as out:out.write(template)
with (D/'manifest.json').open('xb') as out:out.write(raw)
cfgpath=Path('C:/Users/Administrator/.ollama/models/blobs')/config['config']['digest'].replace(':','-')
cfg=cfgpath.read_bytes();assert len(cfg)==config['config']['size'] and hashlib.sha256(cfg).hexdigest()==config['config']['digest'][7:]
with (D/'model-config.json').open('xb') as out:out.write(cfg)
receipt=dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),manifest_sha256=hashlib.sha256(raw).hexdigest(),model_blob=str(p),
    model_blob_declared_sha256=layers[0]['digest'][7:],full_model_blob_rehashed=False,observed_file_bytes=before.st_size,unchanged_stat=True,
    GGUF_version=version,tensor_count=tensors,metadata_pairs=pairs,metadata_end=end,metadata_sha256=hashlib.sha256(prefix).hexdigest(),
    values={k:v for k,v in values.items() if k!='tokenizer.chat_template'},template_bytes=len(template.encode()),
    template_sha256=hashlib.sha256(template.encode()).hexdigest(),has_enable_thinking='enable_thinking' in template,
    metadata_keys=keys,layout_reference='upstream/gguf.h at ggml-org/llama.cpp b10488',
    model_calls=0,network_calls=0,service_operations=0,tensor_data_read=False)
with (D/'metadata-readback.json').open('x',encoding='utf8') as out:json.dump(receipt,out,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k not in ('model_blob','metadata_keys')},ensure_ascii=False))
