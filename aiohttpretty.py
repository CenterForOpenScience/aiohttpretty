import sys
import copy
import json
import asyncio
import collections
from unittest.mock import Mock

from yarl import URL
from furl import furl
from multidict import CIMultiDict
from aiohttp import ClientSession
from aiohttp.helpers import TimerNoop
from aiohttp.streams import StreamReader
from aiohttp.client import ClientResponse
from aiohttp.base_protocol import BaseProtocol


# TODO: Add static type checker with `mypy`
# TODO: Update docstr for most methods

class ImmutableFurl:

    def __init__(self, url, params=None):
        self._url = url
        self._furl = furl(url)
        self._params = furl(url).args
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


class _MockStream(StreamReader):

    def __init__(self, data):

        protocol = BaseProtocol(Mock())
        super().__init__(protocol)

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


def build_raw_headers(headers):
    """Convert a dict of headers to a tuple of tuples. Mimics the format of ClientResponse.
    """
    raw_headers = []
    for k, v in headers.items():
        raw_headers.append((k.encode('utf8'), v.encode('utf8')))
    return tuple(raw_headers)


class _AioHttPretty:

    def __init__(self):

        self.calls = []
        self.registry = {}
        self.request = None

    def make_call(self, **kwargs):
        return kwargs

    async def process_request(self, **kwargs):
        """Process request options as if the request was actually executed.
        """
        data = kwargs.get('data')
        if isinstance(data, asyncio.StreamReader):
            await data.read()

    async def fake_request(self, method, uri, **kwargs):

        params = kwargs.get('params', None)
        url = ImmutableFurl(uri, params=params)

        try:
            response = self.registry[(method, url)]
        except KeyError:
            raise Exception(
                'No URLs matching {method} {uri} with params {url.params}.'
                ' Not making request. Go fix your test.'.format(**locals())
            )

        if isinstance(response, collections.Sequence):
            try:
                response = response.pop(0)
            except IndexError:
                raise Exception('No responses left.')

        await self.process_request(**kwargs)
        self.calls.append(self.make_call(
            method=method,
            uri=ImmutableFurl(uri, params=kwargs.pop('params', None)),
            **kwargs
        ))

        # For how to mock ``ClientResponse`` for ``aiohttp>=3.1.0``, refer to the following link
        # https://github.com/pnuckowski/aioresponses/blob/master/aioresponses/core.py#L129-L147
        loop = Mock()
        # TODO: Figure out why we need the following two lines.
        loop.get_debug = Mock()
        loop.get_debug.return_value = True

        resp_kwargs = {}
        resp_kwargs['request_info'] = Mock()
        resp_kwargs['writer'] = Mock()
        resp_kwargs['continue100'] = None
        resp_kwargs['timer'] = TimerNoop()
        resp_kwargs['traces'] = []
        resp_kwargs['loop'] = loop
        resp_kwargs['session'] = None

        # When init `ClientResponse`, the second parameter must be of type ``yarl.URL``
        # TODO: Integrate a property of this type to ``ImmutableFurl``.
        y_url = URL(uri)
        mock_response = ClientResponse(method, y_url, **resp_kwargs)

        # Quote "We need to initialize headers manually"
        # TODO: Figure out whether we still need this "auto_length".
        # if response.get('auto_length'):
        #     defaults = {'Content-Length': str(mock_response.content.size)}
        # else:
        #     defaults = {}
        headers = CIMultiDict(response.get('headers', {}))
        raw_headers = build_raw_headers(headers)
        mock_response._headers = headers
        mock_response._raw_headers = raw_headers
        mock_response.status = response.get('status', 200)

        # TODO: Figure out what ``reason`` is and whether we need it.
        # mock_response.reason = response.get('')

        # TODO: can we simplify this "_wrap_content_stream()"
        mock_response.content = _wrap_content_stream(response.get('body', 'aiohttpretty'))

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
        ClientSession._request, self.request = self.fake_request, ClientSession._request

    def deactivate(self):
        ClientSession._request, self.request = self.request, None

    def clear(self):
        self.calls = []
        self.registry = {}

    def compare_call(self, first, second):
        for key, value in first.items():
            if second.get(key) != value:
                return False
        return True

    def has_call(self, uri, check_params=True, **kwargs):
        """Check to see if the given uri was called.  By default will verify that the query params
        match up.  Setting ``check_params`` to `False` will strip params from the *called* uri, not
        the passed-in uri."""
        kwargs['uri'] = ImmutableFurl(uri, params=kwargs.pop('params', None))
        for call in self.calls:
            if not check_params:
                call = copy.deepcopy(call)
                call['uri'] = call['uri'].with_out_params()
            if self.compare_call(kwargs, call):
                return True
        return False


sys.modules[__name__] = _AioHttPretty()
