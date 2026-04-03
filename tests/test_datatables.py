"""Tests for DataTablesRequest form and encoding behavior."""

from importlib import import_module
from urllib.parse import parse_qs

DataTablesRequest = import_module("volumeleaders._datatables").DataTablesRequest


def test_encode_contains_columns_pagination_and_ordering() -> None:
    """Encode DataTables fields into a valid URL-encoded body string."""
    request = DataTablesRequest(
        columns=["Ticker", "Dollars"],
        start=25,
        length=100,
        order_column_index=1,
        order_direction="asc",
    )

    encoded = request.encode()
    parsed = parse_qs(encoded)

    assert parsed["columns[0][data]"] == ["Ticker"]
    assert parsed["columns[1][data]"] == ["Dollars"]
    assert parsed["start"] == ["25"]
    assert parsed["length"] == ["100"]
    assert parsed["order[0][column]"] == ["1"]
    assert parsed["order[0][dir]"] == ["asc"]


def test_encode_includes_custom_filters_and_excludes_none() -> None:
    """Include provided filters while dropping filters explicitly set to None."""
    request = DataTablesRequest(
        columns=["Ticker"],
        custom_filters={
            "Tickers": "SPY,QQQ",
            "MinDollars": 500000,
            "DarkPools": True,
            "Ignored": None,
        },
    )

    parsed = parse_qs(request.encode())
    assert parsed["Tickers"] == ["SPY,QQQ"]
    assert parsed["MinDollars"] == ["500000"]
    assert parsed["DarkPools"] == ["True"]
    assert "Ignored" not in parsed


def test_default_values_are_applied() -> None:
    """Use default draw, start, and length when not overridden."""
    request = DataTablesRequest(columns=["Ticker"])
    parsed = parse_qs(request.encode())

    assert parsed["draw"] == ["1"]
    assert parsed["start"] == ["0"]
    assert parsed["length"] == ["50"]


def test_to_form_data_returns_expected_structure() -> None:
    """Build expected DataTables form structure as a flat dictionary."""
    request = DataTablesRequest(
        columns=["Ticker"],
        custom_filters={"StartDate": "2026-04-01"},
    )

    form_data = request.to_form_data()

    assert form_data["draw"] == 1
    assert form_data["start"] == 0
    assert form_data["length"] == 50
    assert form_data["columns[0][data]"] == "Ticker"
    assert form_data["columns[0][searchable]"] == "true"
    assert form_data["columns[0][orderable]"] == "true"
    assert form_data["columns[0][search][value]"] == ""
    assert form_data["order[0][column]"] == 0
    assert form_data["order[0][dir]"] == "desc"
    assert form_data["StartDate"] == "2026-04-01"
