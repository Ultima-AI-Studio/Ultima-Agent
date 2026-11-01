"""Thin adapter for the official sherpa-onnx streaming keyword spotter."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[2]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_files(model_dir, files):
    model_dir=Path(model_dir).resolve()
    for relative, expected in files.items():
        path=(model_dir/relative).resolve()
        if not path.is_relative_to(model_dir):
            raise ValueError('Model manifest path escapes isolated directory')
        if sha256(path).lower()!=expected.lower():
            raise ValueError(f'Model checksum mismatch: {relative}')


class NativeKws:
    def __init__(self, official_spotter, keyword):
        self.kws=official_spotter
        self.keyword=keyword
        self.reset_all()

    def reset_all(self):
        self.stream=self.kws.create_stream()
        self.samples_consumed=0

    def forward(self, pcm):
        if len(pcm)%2:
            raise ValueError('Expected complete PCM16 samples')
        if not pcm:return {}
        import numpy as np
        samples=np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768
        self.stream.accept_waveform(16000,samples)
        self.samples_consumed+=len(samples)
        event={}
        while self.kws.is_ready(self.stream):
            self.kws.decode_stream(self.stream)
            word=self.kws.get_result(self.stream)
            if word:
                if not event:
                    event={'state':1,'keyword':word,'observed_audio_seconds':self.samples_consumed/16000,
                           'score':None,'start':None,'end':None}
                self.kws.reset_stream(self.stream)
        return event


def build_kws(config):
    threshold=float(config['threshold'])
    if not 0<threshold<=1:raise ValueError('KWS threshold must be finite and in (0, 1]')
    import sherpa_onnx
    lock=json.loads((ROOT/'config/voice-next/sherpa-kws.lock.json').read_text(encoding='utf-8'))
    if sherpa_onnx.__version__!=lock['sherpa_onnx_version']:
        raise ValueError('sherpa-onnx version does not match the live lock')
    model=(ROOT/lock['model_dir']).resolve()
    if not model.is_relative_to((ROOT/'models/voice-next').resolve()):
        raise ValueError('Live model must use the isolated new directory')
    verify_files(model,lock['files'])
    keyword=config['keyword']
    if keyword!='你好问问':raise ValueError('This validated profile supports only 你好问问')
    keywords=ROOT/'config/voice-next/keywords.txt'
    tokens={line.rsplit(maxsplit=1)[0] for line in (model/'tokens.txt').read_text(encoding='utf-8').splitlines()}
    lines=keywords.read_text(encoding='utf-8').splitlines()
    if not lines:raise ValueError('Empty keyword profile')
    for line in lines:
        phones,label=line.rsplit(' @',1)
        if label!=keyword or any(phone not in tokens for phone in phones.split()):
            raise ValueError('Keyword pronunciation does not match the pinned model')
    roles=lock['roles']
    official=sherpa_onnx.KeywordSpotter(
        tokens=str(model/'tokens.txt'),encoder=str(model/roles['encoder']),
        decoder=str(model/roles['decoder']),joiner=str(model/roles['joiner']),
        keywords_file=str(keywords),num_threads=2,keywords_score=1,
        keywords_threshold=threshold,num_trailing_blanks=1,
        max_active_paths=8,provider='cpu')
    metadata={'engine':'sherpa-onnx Zipformer native streaming','model':lock['name'],
              'model_sha256':lock['files'][roles['encoder']],'model_files_sha256':lock['files'],
              'sherpa_onnx_version':sherpa_onnx.__version__,'keyword':keyword,
              'keyword_sha256':sha256(keywords),'threshold':threshold,
              'keywords_score':1,'num_trailing_blanks':1,'max_active_paths':8,
              'backend_sha256':sha256(__file__)}
    return NativeKws(official,keyword),metadata
