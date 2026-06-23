"""Angle and risk metric calculations for wrinkle defects."""

from __future__ import annotations

import numpy as np
import pandas as pd

from wrinkle_life_risk.config import ColumnMap


def add_angle_and_risk(
    data: pd.DataFrame,
    columns: ColumnMap = ColumnMap(),
    include_width_weighted: bool = False,
) -> pd.DataFrame:
    """Add theta and risk-score columns to a cleaned defect dataframe."""

    frame = data.copy()
    complete = frame.get("is_complete_for_risk", pd.Series(False, index=frame.index))

    # Geometric angular deviation:
    # theta = arctan(pi * D / W). When depth is unavailable, H/2 is used
    # as the effective measure by the cleaning layer.
    ratio = np.where(
        complete,
        (np.pi * frame["effective_measure"]) / frame[columns.width],
        np.nan,
    )
    frame["theta_rad"] = np.arctan(ratio)
    frame["theta_degree"] = np.degrees(frame["theta_rad"])
    frame["risk_score"] = frame["theta_degree"] * frame["effective_measure"]

    if include_width_weighted:
        valid_width = frame[columns.width].notna() & (frame[columns.width] > 0)
        mean_width = frame.loc[valid_width, columns.width].mean()
        frame["width_weighted_risk"] = np.where(
            complete & valid_width & bool(pd.notna(mean_width) and mean_width > 0),
            frame["risk_score"] * (frame[columns.width] / mean_width),
            np.nan,
        )

    return frame
