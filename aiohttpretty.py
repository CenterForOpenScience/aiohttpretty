import sys
import copy
import json
import asyncio
import collections
from unittest import mock

import furl
import aiohttp
import aiohttp.streams


class ImmutableFurl:

    def __init__(self, url, params=None):
        self._url = url
        self._furl = furl.furl(url)
        self._params = furl.furl(url).args
        self._furl.set(args={})

        params = params or {}
        for (k, v) in params.items():
            self._params.add(k, v)

    def with_out_params(self):
        return ImmutableFurl(self.url)

    @property
    def url(self):
        return self._furl.url

    @property
    def params(self):
        return self._params

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash(self.url + ''.join([
            self.params[x] or ''
            for x in sorted(self.params)
        ]))

class _MockStream(aiohttp.streams.StreamReader):
    def __init__(self, data):
        super().__init__()
        if isinstance(data, str):
            data = data.encode('UTF-8')
        elif not isinstance(data, bytes):
            raise TypeError('Data must be either str or bytes, found {!r}'.format(type(data)))

        self.size = len(data)
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
        params = kwargs.get('params', None)
        url = ImmutableFurl(uri, params=params)

        try:
            response = self.registry[(method, url)]
        except KeyError:
            raise Exception(
                'No URLs matching {method} {uri} with params {url.params}. Not making request. '
                'Go fix your test.'.format(**locals())
            )

        if isinstance(response, collections.Sequence):
            try:
                response = response.pop(0)
            except IndexError:
                raise Exception('No responses left.')

        yield from self.process_request(**kwargs)
        self.calls.append(
            self.make_call(method=method, uri=ImmutableFurl(uri, params=kwargs.pop('params', None)),
                           **kwargs)
        )
        mock_response = aiohttp.client.ClientResponse(method, uri)
        mock_response.content = _wrap_content_stream(response.get('body', 'aiohttpretty'))
        mock_response._loop = mock.Mock()

        if response.get('auto_length'):
            defaults = {
                'Content-Length': str(mock_response.content.size)
            }
        else:
            defaults = {}

        mock_response.headers = aiohttp.multidict.CIMultiDict(response.get('headers', defaults))
        mock_response.status = response.get('status', 200)
        return mock_response

    def register_uri(self, method, uri, **options):
        if any(x.get('params') for x in options.get('responses', [])):
                raise ValueError('Cannot specify params in responses, call register multiple times.')

        params = options.pop('params', {})
        url = ImmutableFurl(uri, params=params)

        self.registry[(method, url)] = options.get('responses', options)

    def register_json_uri(self, method, uri, **options):
        body = json.dumps(options.pop('body', None)).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        headers.update(options.pop('headers', {}))
        self.register_uri(method, uri, body=body, headers=headers, **options)

    def activate(self):
        aiohttp.ClientSession._request, self.request = self.fake_request, aiohttp.ClientSession._request

    def deactivate(self):
        aiohttp.ClientSession._request, self.request = self.request, None

    def clear(self):
        self.calls = []
        self.registry = {}

    def compare_call(self, first, second):
        for key, value in first.items():
            if second.get(key) != value:
                return False
        return True

    def has_call(self, uri, check_params=True, **kwargs):
        kwargs['uri'] = ImmutableFurl(uri, params=kwargs.pop('params', None))

        for call in self.calls:
            if not check_params:
                call = copy.deepcopy(call)
                call['uri'] = call['uri'].with_out_params()
            if self.compare_call(kwargs, call):
                return True
        return False


sys.modules[__name__] = _AioHttPretty()
