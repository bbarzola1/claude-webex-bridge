"""Tests for webex_api.py: retry logic, rate-limit handling, transient error handling."""

import os
import sys

os.environ.setdefault("WEBEX_BOT_TOKEN", "test-token")
os.environ.setdefault("WEBEX_USER_EMAIL", "test@example.com")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from webex_api import WebexAPI


def _make_response(status_code, json_data=None, headers=None):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.json.return_value = json_data or {}
    resp.request = MagicMock()
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=resp.request, response=resp
        )
    return resp


@pytest.fixture
def api():
    """Create a WebexAPI with a mocked httpx client."""
    instance = WebexAPI()
    instance._client = AsyncMock(spec=httpx.AsyncClient)
    return instance


class TestRequestRetry:
    @pytest.mark.asyncio
    async def test_success_on_first_try(self, api):
        api._client.request.return_value = _make_response(200, {"ok": True})
        result = await api._request("GET", "/test")
        assert result == {"ok": True}
        assert api._client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_rate_limit_retry_succeeds(self, api):
        rate_limited = _make_response(429, headers={"Retry-After": "1"})
        success = _make_response(200, {"ok": True})
        api._client.request.side_effect = [rate_limited, success]

        with patch("webex_api.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await api._request("GET", "/test")

        assert result == {"ok": True}
        assert api._client.request.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_rate_limit_retry_after_capped_at_60(self, api):
        rate_limited = _make_response(429, headers={"Retry-After": "999"})
        success = _make_response(200, {"ok": True})
        api._client.request.side_effect = [rate_limited, success]

        with patch("webex_api.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await api._request("GET", "/test")

        assert result == {"ok": True}
        # Should be capped at 60, not 999
        mock_sleep.assert_called_once_with(60)

    @pytest.mark.asyncio
    async def test_rate_limit_invalid_retry_after_defaults_to_5(self, api):
        rate_limited = _make_response(429, headers={"Retry-After": "Thu, 01 Jan 2026 00:00:00 GMT"})
        success = _make_response(200, {"ok": True})
        api._client.request.side_effect = [rate_limited, success]

        with patch("webex_api.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            result = await api._request("GET", "/test")

        assert result == {"ok": True}
        mock_sleep.assert_called_once_with(5)

    @pytest.mark.asyncio
    async def test_rate_limit_exhausted_raises(self, api):
        rate_limited = _make_response(429, headers={"Retry-After": "0"})
        api._client.request.return_value = rate_limited

        with patch("webex_api.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.HTTPStatusError, match="Retries exhausted"):
                await api._request("GET", "/test")

        assert api._client.request.call_count == 3

    @pytest.mark.asyncio
    async def test_401_raises_system_exit(self, api):
        api._client.request.return_value = _make_response(401)

        with pytest.raises(SystemExit):
            await api._request("GET", "/test")

    @pytest.mark.asyncio
    async def test_server_error_retries_then_succeeds(self, api):
        error_500 = _make_response(500)
        success = _make_response(200, {"ok": True})
        api._client.request.side_effect = [error_500, success]

        with patch("webex_api.asyncio.sleep", new_callable=AsyncMock):
            result = await api._request("GET", "/test")

        assert result == {"ok": True}
        assert api._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_network_error_retries_then_succeeds(self, api):
        api._client.request.side_effect = [
            httpx.ConnectError("connection refused"),
            _make_response(200, {"ok": True}),
        ]

        with patch("webex_api.asyncio.sleep", new_callable=AsyncMock):
            result = await api._request("GET", "/test")

        assert result == {"ok": True}
        assert api._client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_network_error_exhausted_raises(self, api):
        api._client.request.side_effect = httpx.ConnectError("connection refused")

        with patch("webex_api.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.ConnectError):
                await api._request("GET", "/test")

        assert api._client.request.call_count == 3


class TestClientNotStarted:
    @pytest.mark.asyncio
    async def test_raises_runtime_error_without_start(self):
        api = WebexAPI()
        with pytest.raises(RuntimeError, match="Call start"):
            await api._request("GET", "/test")
