"""Data cleaning and effective wrinkle measure calculation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from wrinkle_life_risk.config import ColumnMap


class MissingColumnError(ValueError):
    """Raised when required input columns are not available."""


def _ensure_optional_column(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in frame.columns:
        frame[column] = np.nan
    return frame


def prepare_geometry_columns(data: pd.DataFrame, columns: ColumnMap) -> pd.DataFrame:
    """Return a copy with expected geometry columns converted to numeric values."""

    required = [columns.length, columns.width]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise MissingColumnError(f"Required column(s) missing: {', '.join(missing)}")

    frame = data.copy()
    frame = _ensure_optional_column(frame, columns.depth)
    frame = _ensure_optional_column(frame, columns.height)
    frame = _ensure_optional_column(frame, columns.width)

    for column in (columns.length, columns.depth, columns.height, columns.width):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    return frame


def add_effective_measure(data: pd.DataFrame, columns: ColumnMap = ColumnMap()) -> pd.DataFrame:
    """Add effective measure and row-level quality flags.

    Rules:
    - use depth when present
    - otherwise use height / 2
    - otherwise mark the row as incomplete
    """

    frame = prepare_geometry_columns(data, columns)

    has_depth = frame[columns.depth].notna()
    has_height = frame[columns.height].notna()

    frame["effective_measure"] = np.where(
        has_depth,
        frame[columns.depth],
        np.where(has_height, frame[columns.height] / 2.0, np.nan),
    )
    frame["effective_measure_source"] = np.select(
        [has_depth, has_height],
        ["depth", "height/2"],
        default="missing",
    )

    frame["missing_effective_measure"] = frame["effective_measure"].isna()
    frame["invalid_length"] = frame[columns.length].isna() | (frame[columns.length] <= 0)
    frame["invalid_effective_measure"] = frame["effective_measure"].notna() & (
        frame["effective_measure"] < 0
    )
    frame["invalid_width"] = frame[columns.width].isna() | (frame[columns.width] <= 0)

    frame["is_complete_for_risk"] = (
        ~frame["missing_effective_measure"]
        & ~frame["invalid_length"]
        & ~frame["invalid_effective_measure"]
        & ~frame["invalid_width"]
    )
    frame["data_quality_status"] = frame.apply(_quality_status, axis=1)

    return frame


def _quality_status(row: pd.Series) -> str:
    issues: list[str] = []
    if bool(row["missing_effective_measure"]):
        issues.append("missing_effective_measure")
    if bool(row["invalid_length"]):
        issues.append("invalid_length")
    if bool(row["invalid_effective_measure"]):
        issues.append("invalid_effective_measure")
    if bool(row["invalid_width"]):
        issues.append("invalid_width")
    return "ok" if not issues else ";".join(issues)
