"""Evidence-only transport fixture; imports do not run a model or UI."""
from pathlib import Path
import hashlib
import json
import os
import socket
import uuid

CORPUS = Path(__file__).with_name('corpus.json')
CORPUS_SHA = '9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002'


def install():
    import ddgs
    import httpx
    assert hashlib.sha256(CORPUS.read_bytes()).hexdigest() == CORPUS_SHA
    data = json.loads(CORPUS.read_text(encoding='utf-8-sig'))
    sources = {item['final_url']: item for item in data['sources']}
    assert all(hashlib.sha256(s['body'].encode('utf-8')).hexdigest() == s['decoded_body_sha256'] for s in sources.values())
    observed = []
    original_dns = socket.getaddrinfo

    class Search:
        def text(self, query, max_results=5, **kwargs):
            observed.append({'kind': 'search', 'query': query})
            return [{'title': 'Retained official source ' + str(i), 'href': url,
                     'body': 'Controlled source discovery; read the full body.'}
                    for i, url in enumerate(sources, 1)][:max_results]

    def get(method, url, **kwargs):
        assert method == 'GET' and str(url) in sources, 'Unexpected corpus HTTP request'
        assert kwargs['follow_redirects'] is False and kwargs['timeout'] == 5
        source = sources[str(url)]
        observed.append({'kind': 'GET', 'url': str(url), 'body_sha256': source['decoded_body_sha256']})
        return httpx.Response(200, content=source['body'].encode('utf-8'),
                              headers={'content-type': source['content_type']},
                              request=httpx.Request(method, url))

    def dns(host, port, *args, **kwargs):
        if host in ('127.0.0.1', 'localhost', '::1'):
            return original_dns(host, port, *args, **kwargs)
        if host == 'raw.githubusercontent.com':
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('93.184.216.34', int(port or 443)))]
        raise OSError('Nonfixture public DNS is disabled for controlled replay')

    ddgs.DDGS = Search
    httpx.request = get
    socket.getaddrinfo = dns
    wire_root = os.environ.get('ULTIMA_CORPUS_WIRE_ROOT')
    if wire_root:
        root = Path(wire_root).resolve()
        assert root.is_relative_to(CORPUS.parent.parent.resolve()), 'Observer path outside owned evidence'
        root.mkdir(parents=True, exist_ok=True)
        original_send = httpx.Client.send

        def send(client, request, *args, **kwargs):
            capture = (request.method == 'POST' and request.url.host in ('127.0.0.1', 'localhost')
                       and request.url.port == 11434 and request.url.path == '/api/chat')
            if not capture:
                return original_send(client, request, *args, **kwargs)
            key = uuid.uuid4().hex
            (root / (key + '.request.entity')).write_bytes(request.content)
            try:
                response = original_send(client, request, *args, **kwargs)
                # Product uses synchronous nonstreaming POST. read() is idempotent.
                (root / (key + '.response.entity')).write_bytes(response.read())
                (root / (key + '.status.json')).write_text(json.dumps({'status': response.status_code}), encoding='utf-8')
                return response
            except Exception as error:
                (root / (key + '.transport-error.json')).write_text(json.dumps({'type': type(error).__name__, 'error': str(error)}), encoding='utf-8')
                raise

        httpx.Client.send = send
    return data, observed


if __name__ == '__main__':
    import runpy
    import sys
    checkout = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent')
    sys.path.insert(0, str(checkout))
    install()
    # Remaining argv are the ordinary isolated server's original flags.
    runpy.run_module('src.brain.agent_server', run_name='__main__')
