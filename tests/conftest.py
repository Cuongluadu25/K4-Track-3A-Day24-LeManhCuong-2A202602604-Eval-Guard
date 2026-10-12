import socket
from types import SimpleNamespace
from unittest.mock import Mock
import sys

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-live", action="store_true", default=False)


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch, request):
    if request.node.get_closest_marker("integration"):
        if not request.config.getoption("--run-live"):
            pytest.skip("Live APIs require explicit --run-live.")
        return
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_pair = socket.socketpair
    creating_pair = False
    def pair(*args, **kwargs):
        # Windows asyncio creates its private wake-up socketpair via loopback TCP.
        nonlocal creating_pair
        creating_pair = True
        try:
            return real_pair(*args, **kwargs)
        finally:
            creating_pair = False
    def blocked(sock, address, *args, **kwargs):
        if creating_pair and isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return real_connect(sock, address, *args, **kwargs)
        raise AssertionError("Unit tests must not use network/API/model downloads.")
    def blocked_ex(sock, address, *args, **kwargs):
        if creating_pair and isinstance(address, tuple) and address[0] in ("127.0.0.1", "::1"):
            return real_connect_ex(sock, address, *args, **kwargs)
        raise AssertionError("Unit tests must not use network/API/model downloads.")
    monkeypatch.setattr(socket, "socketpair", pair)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked_ex)


@pytest.fixture
def openai_client(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-key")
    import json
    client = Mock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
            "winner": "A", "reasoning": "Matches the supplied policy.",
            "scores": {"A": .9, "B": .2}})))])
    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=Mock(return_value=client)))
    return client
