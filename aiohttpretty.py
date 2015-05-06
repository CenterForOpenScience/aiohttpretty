import sys
import json
import asyncio
import collections

import aiohttp


class _MockStream(asyncio.StreamReader):
    def __init__(self, data):
        super().__init__()
        if isinstance(data, str):
            data = data.encode('UTF-8')
        elif not isinstance(data, bytes):
            raise TypeError('Data must be either str or bytes, found {!r}'.format(type(data)))

        self.feed_data(data)
        self.feed_eof()


def _wrap_content_stream(content):
    if isinstance(content, str):
        content = content.encode('utf-8')

    if isinstance(content, bytes):
        return _MockStream(content)

    if hasattr(content, 'read') and asyncio.iscoroutinefunction(content.read):
        return content

    raise TypeError('Content must be of type bytes or str, or implement the stream interface.')


class _AioHttPretty:
    def __init__(self):
        self.calls = []
        self.registry = {}
        self.request = None

    def make_call(self, **kwargs):
        return kwargs

    @asyncio.coroutine
    def process_request(self, **kwargs):
        """Process request options as if the request was actually executed."""
        data = kwargs.get('data')
        if isinstance(data, asyncio.StreamReader):
            yield from data.read()

    @asyncio.coroutine
    def fake_request(self, method, uri, **kwargs):
        try:
            response = self.registry[(method, uri)]
        except KeyError:
            raise Exception('No URLs matching {method} {uri}. Not making request. Go fix your test.'.format(**locals()))
        if isinstance(response, collections.Sequence):
            try:
                response = response.pop(0)
            except IndexError:
                raise Exception('No responses left.')

        yield from self.process_request(**kwargs)
        self.calls.append(self.make_call(method=method, uri=uri, **kwargs))
        mock_response = aiohttp.client.ClientResponse(method, uri)
        mock_response.content = _wrap_content_stream(response.get('body', 'aiohttpretty'))
        mock_response.headers = aiohttp.multidict.CIMultiDict(response.get('headers', {}))
        mock_response.status = response.get('status', 200)
        return mock_response

    def register_uri(self, method, uri, **options):
        responses = options.get('responses')
        value = responses if responses else options
        self.registry[(method, uri)] = value

    def register_json_uri(self, method, uri, **options):
        body = json.dumps(options.pop('body', None)).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        headers.update(options.pop('headers', {}))
        self.register_uri(method, uri, body=body, headers=headers, **options)

    def activate(self):
        aiohttp.request, self.request = self.fake_request, aiohttp.request

    def deactivate(self):
        aiohttp.request, self.request = self.request, None

    def clear(self):
        self.calls = []
        self.registry = {}

    def compare_call(self, first, second):
        for key, value in first.items():
            if second.get(key) != value:
                return False
        return True

    def has_call(self, **kwargs):
        for call in self.calls:
            if self.compare_call(kwargs, call):
                return True
        return False


sys.modules[__name__] = _AioHttPretty()
