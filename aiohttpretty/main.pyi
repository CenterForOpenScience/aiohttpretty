import typing
from http import HTTPStatus

import aiohttp
import typing_extensions

from aiohttpretty.helpers import StreamLike

METHODS = typing.Literal[
    'GET', 'POST', 'PUT', 'PATCH', 'HEAD', 'OPTIONS', 'DELETE'
]
OptionalMapping = typing.Optional[typing.Mapping[str, str]]
BodyType = typing.Union[str, bytes, StreamLike, None]
P = typing_extensions.ParamSpec('P')
T = typing.TypeVar('T')

class ResponseType(typing.TypedDict, total=False):
    status: int
    reason: str
    auto_length: bool
    headers: typing.Mapping[str, str]
    body: typing.Mapping[str, str]

class AioHttPretty:
    def register_uri(
        self,
        method: METHODS,
        uri: str,
        body: BodyType = None,
        headers: OptionalMapping = None,
        params: OptionalMapping = None,
        responses: typing.Optional[typing.List[ResponseType]] = None,
        status: int = HTTPStatus.OK,
        reason: str = '',
        auto_length: bool = False,
    ) -> None: ...
    def register_json_uri(
        self,
        method: METHODS,
        uri: str,
        body: typing.Optional[typing.Any] = None,
        headers: OptionalMapping = None,
        params: OptionalMapping = None,
        responses: typing.Optional[typing.List[ResponseType]] = None,
        status: int = HTTPStatus.OK,
        reason: str = '',
        auto_length: bool = False,
    ) -> None: ...
    def fake_request(
        self,
        method: METHODS,
        uri: str,
        params: OptionalMapping = None,
        data: BodyType = None,
        **kwargs: typing.Any,
    ) -> aiohttp.ClientResponse: ...
    def activate(self) -> None: ...
    def deactivate(self) -> None: ...
    def clear(self) -> None: ...
    def has_call(
        self,
        uri: str,
        check_params: bool = True,
        params: OptionalMapping = None,
    ) -> bool: ...
    def open(self, clear: bool = True) -> typing.ContextManager[None]: ...
    def async_decorate(
        self,
        func: typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, T]],
    ) -> typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, T]]: ...
    def decorate(
        self, func: typing.Callable[P, T]
    ) -> typing.Callable[P, T]: ...
