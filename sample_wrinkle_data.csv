"""End-to-end analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from wrinkle_life_risk.classification import classify_risk
from wrinkle_life_risk.config import ColumnMap, RiskThresholds
from wrinkle_life_risk.data_cleaning import add_effective_measure
from wrinkle_life_risk.fracture_mechanics import (
    add_fracture_life_assessment,
    add_remaining_cycles,
    calculate_delta_k,
    calculate_parametric_delta_k,
)
from wrinkle_life_risk.metrics import add_angle_and_risk


@dataclass(frozen=True)
class AnalysisOptions:
    """Options controlling a full wrinkle-risk analysis run."""

    columns: ColumnMap = ColumnMap()
    risk_thresholds: RiskThresholds | None = None
    include_width_weighted: bool = False
    compute_delta_k: bool = False
    sigma: float | None = None
    a_column: str = "effective_measure"
    compute_parametric_delta_k: bool = False
    delta_k_geometry_factor: float = 1.12
    delta_k_delta_sigma: float = 250.0
    delta_k_unit_conversion: float = 1000.0
    delta_k_driver_column: str = "theta_degree"
    compute_fracture_life: bool = True
    delta_sigma_default: float = 250.0
    geometry_factor_default: float = 1.12
    paris_c_default: float = 1.0e-10
    paris_m_default: float = 3.0
    critical_crack_size_mm_default: float = 5.0
    compute_remaining_cycles: bool = False
    paris_c: float | None = None
    paris_m: float | None = None
    a_critical: float | None = None
    a_critical_column: str | None = None
    integration_steps: int = 1000


@dataclass(frozen=True)
class AnalysisResult:
    """Data and summary information returned by the analysis pipeline."""

    data: pd.DataFrame
    thresholds: RiskThresholds
    summary: dict[str, object]


def run_analysis(data: pd.DataFrame, options: AnalysisOptions | None = None) -> AnalysisResult:
    """Run cleaning, metric calculation, classification, and optional life estimates."""

    opts = options or AnalysisOptions()

    frame = add_effective_measure(data, opts.columns)
    frame = add_angle_and_risk(
        frame,
        columns=opts.columns,
        include_width_weighted=opts.include_width_weighted,
    )
    frame, thresholds = classify_risk(frame, thresholds=opts.risk_thresholds)

    if opts.compute_delta_k:
        if opts.sigma is None:
            raise ValueError("sigma is required when compute_delta_k is True.")
        frame = calculate_delta_k(
            frame,
            sigma=opts.sigma,
            a_column=opts.a_column,
            geometry_factor=opts.delta_k_geometry_factor,
            unit_conversion=opts.delta_k_unit_conversion,
        )

    if opts.compute_parametric_delta_k:
        frame = calculate_parametric_delta_k(
            frame,
            geometry_factor=opts.delta_k_geometry_factor,
            delta_sigma=opts.delta_k_delta_sigma,
            unit_conversion=opts.delta_k_unit_conversion,
            driver_column=opts.delta_k_driver_column,
        )

    if opts.compute_fracture_life:
        frame = add_fracture_life_assessment(
            frame,
            delta_sigma_default=opts.delta_sigma_default,
            geometry_factor_default=opts.geometry_factor_default,
            paris_c_default=opts.paris_c_default,
            paris_m_default=opts.paris_m_default,
            critical_crack_size_mm_default=opts.critical_crack_size_mm_default,
        )

    if opts.compute_remaining_cycles:
        if opts.sigma is None:
            raise ValueError("sigma is required when compute_remaining_cycles is True.")
        if opts.paris_c is None or opts.paris_m is None:
            raise ValueError("paris_c and paris_m are required for remaining cycles.")
        frame = add_remaining_cycles(
            frame,
            sigma=opts.sigma,
            c_value=opts.paris_c,
            m_value=opts.paris_m,
            a_initial_column=opts.a_column,
            a_critical=opts.a_critical,
            a_critical_column=opts.a_critical_column,
            steps=opts.integration_steps,
            geometry_factor=opts.delta_k_geometry_factor,
            unit_conversion=opts.delta_k_unit_conversion,
        )

    return AnalysisResult(data=frame, thresholds=thresholds, summary=build_summary(frame))


def build_summary(data: pd.DataFrame) -> dict[str, object]:
    """Create compact summary metrics for UI and reports."""

    complete = int(data["is_complete_for_risk"].sum()) if "is_complete_for_risk" in data else 0
    total = int(len(data))
    class_counts = (
        data["risk_class"].value_counts(dropna=False).to_dict() if "risk_class" in data else {}
    )

    summary: dict[str, object] = {
        "row_count": total,
        "complete_for_risk_count": complete,
        "incomplete_or_invalid_count": total - complete,
        "risk_class_counts": class_counts,
    }

    if "risk_score" in data and data["risk_score"].notna().any():
        summary["max_risk_score"] = float(data["risk_score"].max())
        summary["mean_risk_score"] = float(data["risk_score"].mean())
        summary["max_risk_defect"] = _row_identifier(data.loc[data["risk_score"].idxmax()])

    if "Delta_K_MPa_sqrt_m" in data and data["Delta_K_MPa_sqrt_m"].notna().any():
        summary["max_delta_k"] = float(data["Delta_K_MPa_sqrt_m"].max())
        summary["max_delta_k_defect"] = _row_identifier(data.loc[data["Delta_K_MPa_sqrt_m"].idxmax()])

    if "remaining_life_cycles" in data and data["remaining_life_cycles"].notna().any():
        clean_life = data["remaining_life_cycles"].dropna()
        summary["min_remaining_life_cycles"] = float(clean_life.min())
        summary["min_life_defect"] = _row_identifier(data.loc[clean_life.idxmin()])

    score_column = _priority_score_column(data)
    priority_columns = [
        column
        for column in ["Wrinkle_ID", "defect_id", "Row_ID", "Severity_Index", "Risk_Skor", "risk_score", "risk_class"]
        if column in data.columns
    ]
    if priority_columns and score_column:
        summary["top_5_priority"] = (
            data.sort_values(score_column, ascending=False, na_position="last")
            .head(5)[priority_columns]
            .to_dict("records")
        )

    return summary


def _row_identifier(row: pd.Series) -> object:
    for column in ("Wrinkle_ID", "defect_id", "Row_ID"):
        if column in row and pd.notna(row[column]):
            return row[column]
    return int(row.name) if row.name is not None else None


def _priority_score_column(data: pd.DataFrame) -> str | None:
    for column in ("Severity_Index", "Risk_Skor", "risk_score"):
        if column in data.columns:
            return column
    return None
