class AioHttPrettyError(Exception):
    """Base class for all AioHttPrettyErrors"""


class NoUrlMatching(AioHttPrettyError, KeyError):
    """No url matches received url with given params and method"""

    def __str__(self) -> str:
        return Exception.__str__(self)


class ExhaustedAllResponses(AioHttPrettyError, IndexError):
    """No response left for given url"""


class InvalidBody(AioHttPrettyError, TypeError):
    """Received invalid body type"""


class InvalidResponses(AioHttPrettyError, ValueError):
    """Cannot specify params in responses"""
