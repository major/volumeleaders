"""Shared Pydantic model primitives for the VolumeLeaders client."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict

from volumeleaders._parsing import parse_aspnet_date


def _coerce_aspnet_date(value: object) -> datetime | None:
    """Convert ASP.NET date strings into timezone-aware datetimes.

    Accepts values like ``/Date(1775001600000)/`` and returns UTC datetimes.
    Returns ``None`` for API null sentinels and empty values.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        return parse_aspnet_date(value)

    return None


AspNetDate = Annotated[datetime | None, BeforeValidator(_coerce_aspnet_date)]


class VLBaseModel(BaseModel):
    """Base model with alias population enabled for API field names."""

    model_config = ConfigDict(populate_by_name=True)
