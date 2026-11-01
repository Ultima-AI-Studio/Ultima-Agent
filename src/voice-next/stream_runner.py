"""Offline-only adapter for pinned upstream WeKws continuous-stream KWS.

No microphone or playback imports. Does not change the legacy voice service.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import wave

ROOT = Path(__file__).resolve().parents[2]
WEKWS_COMMIT = '6a45aeb994dd81c0969ff877a5a7c46d60ed0c86'
WENET_COMMIT = '1a94771df418325fd335b0b53776f83d74a8111d'
MODEL_REL = 'models/voice-next/wekws-wenwen-fsmn-ctc'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def replay_wav(spotter, path, chunk_samples=4800):
    """Feed every PCM frame once; emit each packet result without waiting for EOS."""
    if chunk_samples <= 0:
        raise ValueError('chunk_samples must be positive')
    with wave.open(str(path), 'rb') as audio:
        if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (1, 2, 16000):
            raise ValueError('Expected mono PCM16 16000 Hz WAV; resample the full file separately')
        total = audio.getnframes()
        if total == 0:
            raise ValueError('Empty audio is not a KWS test')
        consumed = 0
        spotter.reset_all()
        try:
            while pcm := audio.readframes(chunk_samples):
                started = time.perf_counter()
                event = spotter.forward(pcm)
                elapsed = time.perf_counter() - started
                consumed += len(pcm) // 2
                yield {'samples_consumed': consumed, 'audio_seconds': consumed / 16000,
                       'packet_samples': len(pcm) // 2, 'processing_ms': elapsed * 1000,
                       'before_file_end': consumed < total,
                       'event': event if event and event.get('state') == 1 else None}
        finally:
            spotter.reset_all()


def verify_model(model_dir):
    manifest = json.loads((model_dir / 'upstream-files.json').read_text(encoding='utf-8-sig'))
    for item in manifest:
        if item['Type'] != 'blob':
            continue
        path = model_dir / item['Path']
        if not path.resolve().is_relative_to(model_dir.resolve()):
            raise ValueError('Model manifest path escapes model directory')
        if sha256(path).lower() != item['Sha256'].lower():
            raise ValueError(f'Model checksum mismatch: {item["Path"]}')
    return manifest


def build_spotter(model_dir, derived_dir, keyword, threshold):
    """Use upstream model/feature/decoder code, with upstream dictionary conversion."""
    if not keyword or ',' in keyword or any(c.isspace() for c in keyword):
        raise ValueError('Exactly one explicit keyword is required for this proof')
    if not 0 < threshold <= 1:
        raise ValueError('Choose an explicit fixed threshold in (0, 1]')
    verify_model(model_dir)
    wekws = ROOT / 'tools/voice-next/source' / f'wekws-{WEKWS_COMMIT}'
    wenet = ROOT / 'tools/voice-next/source' / f'wenet-{WENET_COMMIT}'
    tokenizer = ROOT / "tools/voice-next/tokenizer-only"
    for name in ("wenet/text/char_tokenizer.py", "wenet/text/base_tokenizer.py", "wenet/utils/file_utils.py"):
        if sha256(tokenizer/name) != sha256(wenet/name):
            raise ValueError("Tokenizer must match pinned upstream source")
    for path in (wekws, tokenizer):
        if not path.is_dir():
            raise FileNotFoundError(path)
        sys.path.insert(0, str(path))
    sys.dont_write_bytecode = True
    # Enforce safe tensor-only loading even through the upstream loader.
    os.environ['TORCH_FORCE_WEIGHTS_ONLY_LOAD'] = '1'
    import torch
    import yaml
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    from wekws.bin.stream_kws_ctc import KeyWordSpotter
    config = yaml.safe_load((model_dir / 'config.yaml').read_text(encoding='utf-8'))
    config['model']['cmvn']['cmvn_file'] = str((model_dir / 'global_cmvn.kaldi').resolve())
    output_dim = config['model']['output_dim']
    # Official recipe: run_fsmn_ctc.sh converts IDs by -1, then '& 1' to filler.
    converted = []
    mapping = {}
    for line in (model_dir / 'tokens.txt').read_text(encoding='utf-8').splitlines():
        token, raw_index = line.rsplit(maxsplit=1)
        index = int(raw_index) - 1
        if token == '&' and index == 1:
            token = '<filler>'
        mapping[token] = index
        converted.append(f'{token} {index}')
    if mapping.get('<blk>') != 0:
        raise ValueError('Upstream decoder requires blank ID 0')
    if any(c not in mapping or not 0 <= mapping[c] < output_dim for c in keyword):
        raise ValueError('Keyword has missing or incompatible model tokens')
    derived_dir.mkdir(parents=True, exist_ok=True)
    (derived_dir / 'dict.txt').write_text('\n'.join(converted) + '\n', encoding='utf-8')
    (derived_dir / 'words.txt').write_text('<SILENCE>\n<EPS>\n<BLK>\n', encoding='utf-8')
    derived_config = derived_dir / 'config.yaml'
    derived_config.write_text(yaml.safe_dump(config,allow_unicode=True),encoding='utf-8')
    spotter = KeyWordSpotter(str(model_dir / 'avg_30.pt'), str(derived_config),
                            str(derived_dir), threshold, gpu=-1)
    spotter.set_keywords(keyword)
    metadata = {'engine': 'WeKws FSMN CTC', 'source_commit': WEKWS_COMMIT,
                'wenet_commit': WENET_COMMIT, 'torch': torch.__version__,
                'python': sys.version, 'keyword': keyword, 'threshold': threshold,
                'keyword_ids': [mapping[c] for c in keyword], 'output_dim': output_dim,
                'model_sha256': sha256(model_dir/'avg_30.pt'),
                'upstream_manifest_sha256': sha256(model_dir/'upstream-files.json'),
                'dictionary_sha256': sha256(derived_dir/'dict.txt'),
                'official_runtime': str(wekws/'wekws/bin/stream_kws_ctc.py'),
                'official_runtime_sha256': sha256(wekws/'wekws/bin/stream_kws_ctc.py'),
                'metric_scope': 'offline technical proof only'}
    return spotter, metadata, torch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wav', type=Path, required=True)
    parser.add_argument('--keyword', default='你好问问')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='Fixed proof operating point; not a calibrated production threshold')
    parser.add_argument('--model-dir', type=Path, default=ROOT / MODEL_REL)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    spotter, metadata, torch = build_spotter(args.model_dir, ROOT/'config/voice-next/wekws',
                                           args.keyword, args.threshold)
    with torch.inference_mode():
        packets = list(replay_wav(spotter, args.wav))
    hits = [packet for packet in packets if packet['event']]
    consumed = sum(p['packet_samples'] for p in packets)
    result = {'metadata': metadata, 'audio': str(args.wav.resolve()),
              'audio_sha256': sha256(args.wav), 'audio_seconds': consumed / 16000,
              'packets': packets, 'hits': hits,
              'processing_rtf': sum(p['processing_ms'] for p in packets)/1000/(consumed/16000),
              'quality_metrics': {'false_wakes_per_hour': None, 'recall': None,
                                  'word_end_latency_ms': None},
              'production_switched': False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'keyword':args.keyword,'hits':len(hits),
                      'hit_before_file_end':any(h['before_file_end'] for h in hits),
                      'processing_rtf':result['processing_rtf'],'receipt':str(args.output)},ensure_ascii=False))

if __name__ == '__main__':
    main()
