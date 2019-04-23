# aiohttpretty

A simple ``asyncio`` compatible ``httpretty`` mock using ``aiohttp``. Tells ``aiohttp`` to return bespoke payloads from certain urls.  If ``aiohttp`` is used to access a url that isn't mocked, throws an error to prevent tests from making live requests.


## Synopsis

```
import myproject

import pytest
import aiohttpretty


@pytest.mark.asyncio
async def test_get_keys_foo():
    good_response = {'dog': 'woof', 'duck': 'quack'}
    good_url = 'http://example.com/dict'
    aiohttpretty.register_json_uri('GET', good_url, body=good_response)

    bad_response = ['dog', 'duck']
    bad_url = 'http://example.com/list'
    aiohttpretty.register_json_uri('GET', bad_url, body=bad_response)

    aiohttpretty.activate()

    # .get_keys_from_url() calls .keys() on response
    keys_from_good = await myproject.get_keys_from_url(good_url)
    assert keys_from_good == ['dog', 'duck']

    with pytest.raises(exceptions.AttributeError) as exc:
        await myproject.get_keys_from_url(bad_url)

    # aiohttpretty will die screaming that this url hasn't been mocked
    # await myproject.get_keys_from_url('http://example.com/unhandled')

    aiohttpretty.deactivate()
```


## Methods

#### `.register_uri(method, uri, **options)`

Register the specified request with aiohttpretty.  When `aiohttp.request` is called, `aiohttpretty` will look for a request that matches in its registry.  If it finds one, it returns a response defined by the parameters given in `options`.  If no matching request is found, `aiohttpretty` will throw an error.  The HTTP method, uri, and query parameters must all match to be found.

`method`: HTTP method to be issued against the `uri`.

`uri`: The uri to be mocked.

`options`: modifiers to the expected request and the mock response

* `params`: Affects the *request*. These will be added to the registered uri.

* `responses`: Affects the *response*. A list of dicts containing one or more of the following parameters.  Each call to the uri will return the next response in the sequence.

* `status`: Affects the *response*.  The HTTP status code of the response. Defaults to 200.

* `headers`: Affects the *response*. A dict of headers to be included with the response.  Default is *no headers*.

* `body`: Affects the *response*.  The content to be returned when `.read()` is called on the response object.  Must be either `bytes`, `str`, or `instanceOf(asyncio.StreamReader)`.


#### `.register_json_uri(method, uri, **options)`

Same as `.register_uri` but automatically adds a `Content-Type: application/json` header to the response (though this can be overwritten if an explicit `Content-Type` is passed in the `headers` kwarg).  Will also json encode the data structure given in the `body` kwarg.


#### `.fake_request(method, uri, **kwargs)`

`aiohttpretty`'s fake implementation of aiohttp's request method.  Takes the same parameters, but only uses `method`, `uri`, and `params` to lookup the mocked response in the registry.  If the `data` kwarg is set and is an instance of `asyncio.StreamReader`, `.fake_request()` will read the stream to exhaustion to mimic its consumption.


#### `.activate()`

Replaces `aiohttp.ClientSession._request` with `.fake_request()`.  The original implementation is saved.


#### `.deactivate()`

Restores `aiohttp.ClientSession._request` to the saved implementation.


#### `.clear()`

Purge the registry and the list of intercepted calls.


#### `.has_call(uri, check_params=True)`

Checks to see if the given uri was called during the test.  By default, will verify that the query params match up.  Setting `check_params` to `False` will strip params from the *registered* uri, not the passed-in uri.


## Other

### pytest marker

To simplify usage of `aiohttpretty` in tests, you can make a pytest marker that will automatically activate/deactivate `aiohttpretty` for the scope of a test.  To do so, add the following to your `conftest.py`:

```
import aiohttpretty

def pytest_configure(config):
    config.addinivalue_line(
        'markers',
        'aiohttpretty: mark tests to activate aiohttpretty'
    )

def pytest_runtest_setup(item):
    marker = item.get_marker('aiohttpretty')
    if marker is not None:
        aiohttpretty.clear()
        aiohttpretty.activate()

def pytest_runtest_teardown(item, nextitem):
    marker = item.get_marker('aiohttpretty')
    if marker is not None:
        aiohttpretty.deactivate()
```

Then add `@pytest.mark.aiohttpretty` before `async def test_foo`.
