import json
import asyncio
import unittest

import pytest
from aiohttp import ClientSession

import aiohttpretty


def async_test(f):
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    return wrapper


class DummyAsyncStream(asyncio.StreamReader):

    def __init__(self, data):
        super().__init__()
        self.size = len(data)
        self.feed_data(data)
        self.feed_eof()


class TestGeneral(unittest.TestCase):

    def tearDown(self):
        aiohttpretty.clear()

    @async_test
    async def test_fake_request(self):
        desired_response = b'example data'
        url = 'http://example.com/'

        aiohttpretty.register_uri('GET', url, body=desired_response)

        response = await aiohttpretty.fake_request('GET', url)
        data = await response.read()
        assert data == desired_response

    def test_register_uri(self):
        url = 'http://example.com/'
        desired_response = b'example data'

        aiohttpretty.register_uri('GET', url, body=desired_response)
        options = aiohttpretty.registry[('GET', 'http://example.com/')]
        assert options == {'body': b'example data'}

    def test_register_json_uri(self):
        url = 'http://example.com/'
        desired_response = {'test_key': 'test_value'}

        aiohttpretty.register_json_uri('GET', url, body=desired_response)
        options = aiohttpretty.registry[('GET', 'http://example.com/')]
        assert json.loads(options['body'].decode('utf-8')) == desired_response

    @async_test
    async def test_param_handling(self):
        url = 'http://example-params.com/?test=test'
        desired_error_msg = (
            "No URLs matching GET http://example-params.com/?test=test with params {'test': 'test'}. "
            "Not making request. Go fix your test."
        )
        try:
            await aiohttpretty.fake_request('GET', url)
        except Exception as exception:
            assert str(exception) == desired_error_msg

    @async_test
    async def test_params(self):
        desired_response = b'example data'
        url = 'http://example.com/'
        params = {'meow': 'quack', 'woof': 'beans'};

        aiohttpretty.register_uri('GET', url, params=params, body=desired_response)

        response = await aiohttpretty.fake_request('GET',
                                                   'http://example.com/?meow=quack&woof=beans')
        data = await response.read()
        assert data == desired_response

    @async_test
    async def test_str_response_encoding(self):
        aiohttpretty.register_uri('GET',
                                  'http://example.com/',
                                  body='example résumé data')
        response = await aiohttpretty.fake_request('GET',
                                                   'http://example.com/')
        data = await response.read()
        assert data == 'example résumé data'.encode('utf-8')

    @async_test
    async def test_has_call(self):
        aiohttpretty.register_uri('GET',
                                  'http://example.com/',
                                  params={'alpha': '1', 'beta': None},
                                  body='foo')
        response = await aiohttpretty.fake_request('GET',
                                                   'http://example.com/?alpha=1&beta=')
        assert await response.read() == b'foo'

        params_equivalent = [
            'http://example.com/?alpha=1&beta=',
            'http://example.com/?beta=&alpha=1',
        ]
        for uri in params_equivalent:
            assert aiohttpretty.has_call(method='GET', uri=uri)

        params_different = [
            'http://example.com/',
            'http://example.com/?alpha=2&beta=',
            # 'http://example.com/?alpha=1',  # buggy atm
            'http://example.com/?beta=',
            'http://example.com/?alpha=1&beta=1',
            'http://example.com/?alpha=&beta=',
        ]
        for uri in params_different:
            assert not aiohttpretty.has_call(method='GET', uri=uri)

        assert aiohttpretty.has_call(method='GET', uri='http://example.com/',
                                     params={'alpha': '1', 'beta': None})
        assert aiohttpretty.has_call(method='GET', uri='http://example.com/', check_params=False)
        assert not aiohttpretty.has_call(method='POST', uri='http://example.com/?alpha=1&beta=')
        assert not aiohttpretty.has_call(method='GET', uri='http://otherexample.com/')

    def test_activate(self):
        orig_real_id = id(ClientSession._request)
        orig_fake_id = id(aiohttpretty.fake_request)

        assert aiohttpretty.request is None
        assert ClientSession._request != aiohttpretty.fake_request
        assert id(ClientSession._request) == orig_real_id
        assert id(ClientSession._request) != orig_fake_id

        aiohttpretty.activate()

        assert aiohttpretty.request is not None
        assert id(aiohttpretty.request) == orig_real_id

        assert ClientSession._request == aiohttpretty.fake_request
        assert id(ClientSession._request) != orig_real_id
        assert id(ClientSession._request) == orig_fake_id

        aiohttpretty.deactivate()

        assert aiohttpretty.request is None
        assert ClientSession._request != aiohttpretty.fake_request
        assert id(ClientSession._request) == orig_real_id
        assert id(ClientSession._request) != orig_fake_id

    @async_test
    async def test_multiple_responses(self):
        aiohttpretty.register_uri(
            'GET',
            'http://example.com/',
            responses=[
                {
                    'status': 200,
                    'body': 'moo',
                },
                {
                    'status': 200,
                    'body': 'quack',
                },
            ],
        )

        first_resp = await aiohttpretty.fake_request('GET', 'http://example.com/')
        assert await first_resp.read() == b'moo'

        second_resp = await aiohttpretty.fake_request('GET', 'http://example.com/')
        assert await second_resp.read() == b'quack'

        with pytest.raises(Exception) as exc:
            await aiohttpretty.fake_request('GET', 'http://example.com/')

    def test_no_params_in_responses(self):
        with pytest.raises(ValueError):
            aiohttpretty.register_uri(
                'GET',
                'http://example.com/',
                responses=[
                    {
                        'status': 200,
                        'body': 'moo',
                        'params': {'alpha': '1', 'beta': None}
                    },
                ],
            )

        with pytest.raises(ValueError):
            aiohttpretty.register_uri(
                'GET',
                'http://example.com/',
                responses=[
                    {
                        'status': 200,
                        'body': 'woof',
                    },
                    {
                        'status': 200,
                        'body': 'moo',
                        'params': {'alpha': '1', 'beta': None}
                    },
                ],
            )

    @async_test
    async def test_headers_in_response(self):
        aiohttpretty.register_uri('GET', 'http://example.com/',
                                  headers={'X-Magic-Header': '1'})

        first_resp = await aiohttpretty.fake_request('GET', 'http://example.com/')
        assert 'X-Magic-Header' in first_resp.headers

    @async_test
    async def test_async_streaming_body(self):
        stream = DummyAsyncStream(b'meow')
        aiohttpretty.register_uri('GET', 'http://example.com/', body=stream)

        resp = await aiohttpretty.fake_request('GET', 'http://example.com/')
        assert await resp.read() == b'meow'

    @async_test
    async def test_invalid_body(self):
        aiohttpretty.register_uri('GET', 'http://example.com/', body=1234)

        with pytest.raises(TypeError):
            await aiohttpretty.fake_request('GET', 'http://example.com/')

    @async_test
    async def test_passed_data_is_read(self):
        aiohttpretty.register_uri('GET', 'http://example.com/', body='woof')

        stream = DummyAsyncStream(b'meow')
        assert not stream.at_eof()

        resp = await aiohttpretty.fake_request('GET', 'http://example.com/', data=stream)

        assert stream.at_eof()
        assert await resp.read() == b'woof'

    @async_test
    async def test_aiohttp_request(self):
        aiohttpretty.register_uri('GET', 'http://example.com/', body=b'example data')

        aiohttpretty.activate()
        async with ClientSession() as session:
            async with session.get('http://example.com/') as response:
                assert await response.read() == b'example data'
        aiohttpretty.deactivate()
