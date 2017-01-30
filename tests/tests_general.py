import pytest
import aiohttpretty
import unittest
import asyncio
import json

def async_test(f):
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)
    return wrapper

class TestGeneral(unittest.TestCase):

    def tearDown(self):
        aiohttpretty.clear()

    @pytest.mark.asyncio
    @pytest.mark.aiohttpretty
    @async_test
    async def test_fake_request(self):
        desired_response = b'example data'
        url = 'http://example.com/'

        aiohttpretty.register_uri('GET', url, body=desired_response)

        response = await aiohttpretty.fake_request('GET', url)
        data = await response.read()
        assert data == desired_response

    @pytest.mark.asyncio
    @pytest.mark.aiohttpretty
    @async_test
    async def test_register_uri(self):
        url = 'http://example.com/'
        desired_response = b'example data'

        aiohttpretty.register_uri('GET', url, body=desired_response)
        options = aiohttpretty.registry[('GET', 'http://example.com/')]
        assert options == {'body': b'example data'}

    @pytest.mark.asyncio
    @pytest.mark.aiohttpretty
    @async_test
    async def test_register_json_uri(self):
        url = 'http://example.com/'
        desired_response = {'test_key' : 'test_value'}

        aiohttpretty.register_json_uri('GET', url, body=desired_response)
        options = aiohttpretty.registry[('GET', 'http://example.com/')]
        assert json.loads(options['body']) == desired_response


    @pytest.mark.asyncio
    @pytest.mark.aiohttpretty
    @async_test
    async def test_param_handling(self):
        url = 'http://example-params.com/?test=test'
        desired_error_msg = "No URLs matching GET http://example-params.com/?test=test with params {'test': 'test'}. " \
                            "Not making request. Go fix your test."

        try:
            await aiohttpretty.fake_request('GET', url)
        except Exception as exception:
            assert str(exception) == desired_error_msg
