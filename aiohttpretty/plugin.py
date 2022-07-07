import pytest

from .main import aiohttpretty


@pytest.hookimpl
def pytest_runtest_setup(item: pytest.Item):
    if all(mark.name != 'aiohttpretty' for mark in item.iter_markers()):
        return
    aiohttpretty.clear()
    aiohttpretty.activate()


@pytest.hookimpl
def pytest_runtest_teardown(item: pytest.Item):
    if all(mark.name != 'aiohttpretty' for mark in item.iter_markers()):
        return
    aiohttpretty.deactivate()
    aiohttpretty.clear()


def pytest_configure(config):
    config.addinivalue_line(
        'markers', 'aiohttpretty: mark tests to activate aiohttpretty'
    )
