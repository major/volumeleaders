"""Helpers for building DataTables form-encoded request bodies."""

from dataclasses import dataclass, field
from urllib.parse import urlencode


@dataclass(slots=True)
class DataTablesRequest:
    """Build an application/x-www-form-urlencoded DataTables request body."""

    columns: list[str]
    start: int = 0
    length: int = 50
    order_column_index: int = 0
    order_direction: str = "desc"
    custom_filters: dict[str, str | int | float | bool | None] = field(
        default_factory=dict
    )
    draw: int = 1

    def to_form_data(self) -> dict[str, str | int | float | bool]:
        """Return DataTables payload as a flat dictionary of form fields."""
        body: dict[str, str | int | float | bool] = {
            "draw": self.draw,
            "start": self.start,
            "length": self.length,
            "order[0][column]": self.order_column_index,
            "order[0][dir]": self.order_direction,
        }

        for index, column_name in enumerate(self.columns):
            body[f"columns[{index}][data]"] = column_name
            body[f"columns[{index}][name]"] = column_name
            body[f"columns[{index}][searchable]"] = "true"
            body[f"columns[{index}][orderable]"] = "true"
            body[f"columns[{index}][search][value]"] = ""
            body[f"columns[{index}][search][regex]"] = "false"

        for key, value in self.custom_filters.items():
            if value is None:
                continue
            body[key] = value

        return body

    def encode(self) -> str:
        """Return the URL-encoded request body string."""
        return urlencode(self.to_form_data())
