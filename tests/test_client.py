"""Tests for core request methods on VolumeLeadersClient."""

from importlib import import_module
from typing import Any
from unittest.mock import Mock

import pytest

_exceptions = import_module("volumeleaders._exceptions")
APIError = _exceptions.APIError


def test_post_json_raises_api_error_on_non_200(
    mock_client: tuple[Any, Mock],
) -> None:
    """Raise APIError when JSON endpoint returns a non-200 status code."""
    client, http_mock = mock_client
    response = Mock()
    response.status_code = 500
    response.text = "server error"
    http_mock.post.return_value = response

    with pytest.raises(APIError):
        client.post_json("/any/path", {"payload": True})


def test_post_datatables_extracts_data_array(
    mock_client: tuple[Any, Mock],
) -> None:
    """Return the data array from standard DataTables response envelopes."""
    client, http_mock = mock_client
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"data": [{"Ticker": "SPY"}]}
    http_mock.post.return_value = response

    rows = client.post_datatables("/datatable/path", "draw=1")

    assert rows == [{"Ticker": "SPY"}]


def test_post_datatables_raises_when_data_key_missing(
    mock_client: tuple[Any, Mock],
) -> None:
    """Raise APIError when DataTables response omits the expected data key."""
    client, http_mock = mock_client
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"recordsTotal": 1}
    http_mock.post.return_value = response

    with pytest.raises(APIError):
        client.post_datatables("/datatable/path", "draw=1")
