"""Risk classification helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from wrinkle_life_risk.config import RiskThresholds


def resolve_thresholds(
    scores: pd.Series,
    thresholds: RiskThresholds | None = None,
) -> RiskThresholds:
    """Return manual thresholds or explicit default severity thresholds."""

    if thresholds is not None:
        return thresholds

    return RiskThresholds()


def classify_risk(
    data: pd.DataFrame,
    score_column: str = "risk_score",
    thresholds: RiskThresholds | None = None,
) -> tuple[pd.DataFrame, RiskThresholds]:
    """Add a LOW/MEDIUM/HIGH/CRITICAL/INCOMPLETE risk class column."""

    frame = data.copy()
    resolved = resolve_thresholds(frame[score_column], thresholds)
    frame["risk_class"] = frame[score_column].apply(lambda value: _classify_value(value, resolved))
    return frame, resolved


def _classify_value(value: float, thresholds: RiskThresholds) -> str:
    if value is None or bool(pd.isna(value)):
        return "INCOMPLETE"
    if not np.isfinite(float(value)):
        return "INCOMPLETE"
    if value < thresholds.medium_min:
        return "LOW"
    if value < thresholds.high_min:
        return "MEDIUM"
    if value < thresholds.critical_min:
        return "HIGH"
    return "CRITICAL"
