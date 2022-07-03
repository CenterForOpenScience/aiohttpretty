import typing
from unittest.mock import Mock

from aiohttp.base_protocol import BaseProtocol
from aiohttp.streams import StreamReader
from furl import furl  # type: ignore


class ImmutableFurl:
    def __init__(
        self,
        url: str,
        params: typing.Optional[typing.Mapping[str, str]] = None,
    ):
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
        return hash(
            self.url
            + ''.join(self.params[x] or '' for x in sorted(self.params))
        )


DEFAULT_LIMIT = 2 ** 16


class MockStream(StreamReader):
    def __init__(self, data: typing.Any, limit: int = DEFAULT_LIMIT):
        protocol = BaseProtocol(Mock())
        super().__init__(protocol, limit)
        self.size = len(data)
        self.feed_data(data)
        self.feed_eof()
