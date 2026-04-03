"""Endpoints for alert configs and alert logs."""

from __future__ import annotations

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._datatables import DataTablesRequest
from volumeleaders.endpoints.trades import TRADE_CLUSTER_COLUMNS, TRADE_COLUMNS
from volumeleaders.models import AlertConfig, TradeAlert, TradeClusterAlert

ALERT_CONFIG_COLUMNS = ["Name", "Name", "Tickers", "Conditions"]


def get_alert_configs(client: VolumeLeadersClient) -> list[AlertConfig]:
    """Return saved alert configurations for the authenticated user."""
    request = DataTablesRequest(
        columns=ALERT_CONFIG_COLUMNS,
        start=0,
        length=-1,
        order_column_index=1,
        order_direction="asc",
    )
    rows = client.post_datatables("/AlertConfigs/GetAlertConfigs", request.encode())
    return [AlertConfig.model_validate(row) for row in rows]


def get_trade_alerts(client: VolumeLeadersClient, *, date: str) -> list[TradeAlert]:
    """Return trade alert rows for a single date."""
    request = DataTablesRequest(
        columns=TRADE_COLUMNS,
        start=0,
        length=100,
        order_column_index=1,
        order_direction="desc",
        custom_filters={"Date": date},
    )
    rows = client.post_datatables("/TradeAlerts/GetTradeAlerts", request.encode())
    return [TradeAlert.model_validate(row) for row in rows]


def get_trade_cluster_alerts(
    client: VolumeLeadersClient, *, date: str
) -> list[TradeClusterAlert]:
    """Return trade cluster alert rows for a single date."""
    request = DataTablesRequest(
        columns=TRADE_CLUSTER_COLUMNS,
        start=0,
        length=100,
        order_column_index=1,
        order_direction="desc",
        custom_filters={"Date": date},
    )
    rows = client.post_datatables(
        "/TradeClusterAlerts/GetTradeClusterAlerts", request.encode()
    )
    return [TradeClusterAlert.model_validate(row) for row in rows]
