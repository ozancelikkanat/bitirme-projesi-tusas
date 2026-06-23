"""Configuration objects used by the wrinkle risk pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnMap:
    """Input column names used by the analysis pipeline."""

    length: str = "length"
    width: str = "width"
    depth: str = "depth"
    height: str = "height"
    defect_id: str | None = None


@dataclass(frozen=True)
class RiskThresholds:
    """Thresholds separating LOW/MEDIUM/HIGH/CRITICAL risk classes."""

    medium_min: float = 0.50
    high_min: float = 3.00
    critical_min: float = 15.00

    def __post_init__(self) -> None:
        if not 0 <= self.medium_min < self.high_min < self.critical_min:
            raise ValueError(
                "Risk thresholds must satisfy "
                "0 <= medium_min < high_min < critical_min."
            )
