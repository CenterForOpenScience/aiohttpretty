============
aiohttpretty
============

A simple asyncio compatible httpretty mock using aiohttp.  Tells aiohttp to return bespoke payloads
from certain urls.  If aiohttp is used to access a url that isn't mocked, throws an error to
prevent tests from making live requests.


SYNOPSIS
--------

.. code-block:: python

  import myproject

  import pytest
  import aiohttpretty


  @pytest.mark.asyncio
  @pytest.mark.aiohttpretty
  async def test_get_keys_foo():
      good_response = {'dog': 'woof', 'duck': 'quack'}
      good_url = 'http://example.com/dict'
      aiohttpretty.register_json_uri('GET', good_url, body=good_response)

      bad_response = ['dog', 'duck']
      bad_url = 'http://example.com/list'
      aiohttpretty.register_json_uri('GET', bad_url, body=bad_response)

      # .get_keys_from_url() calls .keys() on response

      keys_from_good = await myproject.get_keys_from_url(good_url)
      assert keys_from_good == ['dog', 'duck']

      with pytest.raises(exceptions.AttributeError) as exc:
          await myproject.get_keys_from_url(bad_url)

      # aiohttpretty will die screaming that this url hasn't been mocked
      # await myproject.get_keys_from_url('http://example.com/unhandled')
