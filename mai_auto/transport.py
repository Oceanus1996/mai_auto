"""OpenAI-compatible wire adapter; never generates or changes prompts."""
import asyncio
import json
from types import SimpleNamespace
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class ModelTransport:
    def __init__(self, base_url, model, timeout=180, mode="local", key_env=None):
        url = urlparse(base_url)
        local = url.scheme == 'http' and url.hostname in ('127.0.0.1', 'localhost', '::1')
        if mode not in ('local', 'api') or (mode == 'local' and not local):
            raise ValueError('Local mode requires a loopback HTTP endpoint')
        if mode == 'api' and (url.scheme != 'https' or not url.hostname):
            raise ValueError('API mode requires an explicit HTTPS endpoint')
        import os
        self.key = os.environ[key_env] if key_env else None
        if mode == 'api' and not self.key:
            raise ValueError('API mode requires key_env naming a populated environment variable')
        if url.username or url.password or url.query or url.fragment:
            raise ValueError('Credentials/query/fragment are not allowed in endpoint')
        self.base_url, self.model, self.timeout = base_url.rstrip('/'), model, timeout
        self.config = SimpleNamespace(primary_model=model)

    def chat(self, messages, *, system=None, max_tokens=None, **kwargs):
        messages = ([{'role': 'system', 'content': system}] if system else []) + list(messages)
        body = {'model': self.model, 'messages': messages, 'temperature': 0.7, **kwargs}
        if max_tokens is not None:
            body['max_tokens'] = max_tokens
        headers = {'Content-Type': 'application/json'}
        if self.key:
            headers['Authorization'] = 'Bearer ' + self.key
        request = Request(self.base_url + '/chat/completions', json.dumps(body).encode(), headers)
        # Disable redirects: a local endpoint must not redirect model requests to a cloud endpoint.
        import urllib.request
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kw):
                return None
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        with opener.open(request, timeout=self.timeout) as response:
            raw = json.load(response)
        content = raw['choices'][0]['message']['content']
        if not isinstance(content, str) or not content.strip():
            raise ValueError('Model returned empty/non-text content')
        return SimpleNamespace(content=content, raw=raw)

    async def response_async(self, messages, **kwargs):
        # Match CoI openai_llm.response_async generation defaults.
        kwargs.setdefault('n', 1)
        kwargs.setdefault('temperature', 0.7)
        kwargs.setdefault('max_tokens', 4000)
        return (await asyncio.to_thread(self.chat, messages, **kwargs)).content
