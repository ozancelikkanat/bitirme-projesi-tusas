"""Fracture mechanics screening helpers."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def calculate_delta_k(
    data: pd.DataFrame,
    sigma: float,
    a_column: str = "effective_measure",
    output_column: str = "delta_k",
    geometry_factor: float = 1.12,
    unit_conversion: float = 1000.0,
) -> pd.DataFrame:
    """Add DeltaK = Y * sigma * sqrt(pi * a_m), converting crack size from mm to m."""

    if sigma <= 0:
        raise ValueError("sigma must be positive.")
    if geometry_factor <= 0:
        raise ValueError("geometry_factor must be positive.")
    if unit_conversion <= 0:
        raise ValueError("unit_conversion must be positive.")

    frame = data.copy()
    a_mm = pd.to_numeric(frame[a_column], errors="coerce")
    a_m = a_mm / unit_conversion
    frame[output_column] = np.where(
        a_m >= 0,
        geometry_factor * sigma * np.sqrt(np.pi * a_m),
        np.nan,
    )
    return frame


def calculate_parametric_delta_k(
    data: pd.DataFrame,
    geometry_factor: float,
    delta_sigma: float,
    unit_conversion: float,
    driver_column: str = "theta_degree",
    output_column: str = "delta_k_parametric",
) -> pd.DataFrame:
    """Add Excel-style DeltaK = Y * DeltaSigma * sqrt(pi * (driver / conversion))."""

    if geometry_factor <= 0:
        raise ValueError("geometry_factor must be positive.")
    if delta_sigma <= 0:
        raise ValueError("delta_sigma must be positive.")
    if unit_conversion <= 0:
        raise ValueError("unit_conversion must be positive.")
    if driver_column not in data.columns:
        raise ValueError(f"DeltaK driver column is missing: {driver_column}")

    frame = data.copy()
    driver = pd.to_numeric(frame[driver_column], errors="coerce")
    normalized_driver = driver / unit_conversion
    frame[output_column] = np.where(
        normalized_driver >= 0,
        geometry_factor * delta_sigma * np.sqrt(np.pi * normalized_driver),
        np.nan,
    )
    return frame


def add_fracture_life_assessment(
    data: pd.DataFrame,
    delta_sigma_default: float = 250.0,
    geometry_factor_default: float = 1.12,
    paris_c_default: float = 1.0e-10,
    paris_m_default: float = 3.0,
    critical_crack_size_mm_default: float = 5.0,
) -> pd.DataFrame:
    """Add preliminary fracture screening outputs.

    Delta_K = Geometry_Factor_Y * Assumed_Stress_MPa * sqrt(pi * Assumed_Crack_m)
    Assumed_Crack_mm defaults to Effective_Size_mm * 0.5 when not supplied.
    Estimated_Life_Cycles = 1 / da_dN, used only as a relative priority
    indicator. It is not a validated remaining-life prediction.
    """

    _validate_positive(delta_sigma_default, "delta_sigma_default")
    _validate_positive(geometry_factor_default, "geometry_factor_default")
    _validate_positive(paris_c_default, "paris_c_default")
    _validate_positive(paris_m_default, "paris_m_default")
    _validate_positive(critical_crack_size_mm_default, "critical_crack_size_mm_default")

    frame = data.copy()
    complete = frame.get("is_complete_for_risk", pd.Series(False, index=frame.index))

    frame["Assumed_Stress_MPa"] = _numeric_input_or_default(
        frame,
        ["Assumed_Stress_MPa", "Delta_sigma_MPa", "DELTA SİGMA", "Delta Sigma", "Delta_sigma"],
        delta_sigma_default,
    )
    frame["Geometry_Factor_Y"] = _numeric_input_or_default(
        frame,
        ["Geometry_Factor_Y", "Geometry_factor_Y", "Y_factor", "Y"],
        geometry_factor_default,
    )
    frame["Paris_C"] = _numeric_input_or_default(
        frame,
        ["Paris_Law_C", "Paris_C", "C"],
        paris_c_default,
    )
    frame["Paris_m"] = _numeric_input_or_default(
        frame,
        ["Paris_Law_m", "Paris_m", "M", "m"],
        paris_m_default,
    )
    frame["Critical_crack_size_mm"] = _numeric_input_or_default(
        frame,
        ["Critical_crack_size_mm", "critical_crack_size_mm", "Critical a"],
        critical_crack_size_mm_default,
    )
    frame["Effective_Size_mm"] = _numeric_input_or_default(
        frame,
        ["Effective_Size_mm", "Effective_Size", "effective_measure"],
        np.nan,
    )
    frame["Assumed_Crack_mm"] = _numeric_input_or_default(
        frame,
        ["Assumed_Crack_mm", "Assumed_Crack"],
        np.nan,
    )
    missing_crack = frame["Assumed_Crack_mm"].isna()
    frame.loc[missing_crack, "Assumed_Crack_mm"] = frame.loc[missing_crack, "Effective_Size_mm"] * 0.5
    frame["Assumed_Crack_m"] = frame["Assumed_Crack_mm"] / 1000.0

    frame["Delta_sigma_MPa"] = frame["Assumed_Stress_MPa"]
    frame["Y_factor"] = frame["Geometry_Factor_Y"]
    frame["critical_crack_size_mm"] = frame["Critical_crack_size_mm"]
    frame["a_mm"] = frame["Assumed_Crack_mm"]
    frame["a_m"] = frame["Assumed_Crack_m"]

    advanced_risk = frame.get(
        "risk_class",
        pd.Series("INCOMPLETE", index=frame.index, dtype="object"),
    ).isin(["MEDIUM", "HIGH", "CRITICAL"])
    valid_inputs = (
        complete
        & advanced_risk
        & (frame["Assumed_Crack_m"] >= 0)
        & (frame["Assumed_Stress_MPa"] > 0)
        & (frame["Geometry_Factor_Y"] > 0)
        & (frame["Paris_C"] > 0)
        & (frame["Paris_m"] > 0)
    )

    frame["Delta_K_MPa_sqrt_m"] = np.where(
        valid_inputs,
        frame["Geometry_Factor_Y"] * frame["Assumed_Stress_MPa"] * np.sqrt(np.pi * frame["Assumed_Crack_m"]),
        np.nan,
    )
    frame["da_dN_m_per_cycle"] = np.where(
        valid_inputs,
        frame["Paris_C"] * np.power(frame["Delta_K_MPa_sqrt_m"], frame["Paris_m"]),
        np.nan,
    )
    frame["Estimated_Life_Cycles"] = np.where(
        valid_inputs & (frame["da_dN_m_per_cycle"] > 0),
        1.0 / frame["da_dN_m_per_cycle"],
        np.nan,
    )
    frame["remaining_life_cycles"] = frame["Estimated_Life_Cycles"]
    valid_life = frame["Estimated_Life_Cycles"].dropna()
    max_life = float(valid_life.max()) if not valid_life.empty else np.nan
    frame["relative_life_index"] = np.where(
        valid_inputs & np.isfinite(max_life) & (max_life > 0),
        frame["Estimated_Life_Cycles"] / max_life * 100.0,
        np.nan,
    )
    frame["inspection_priority"] = inspection_priority_from_life(frame["Estimated_Life_Cycles"])
    frame["fracture_status"] = np.select(
        [valid_inputs, complete & ~advanced_risk],
        ["FRACTURE_SCREENING", "NOT_SELECTED_LOW_RISK"],
        default="INCOMPLETE",
    )

    comments = _build_engineering_comments(frame)
    frame["yorum_özeti"] = comments["yorum_özeti"]
    frame["geometrik_değerlendirme"] = comments["geometrik_değerlendirme"]
    frame["kırılma_mekaniği_değerlendirmesi"] = comments["kırılma_mekaniği_değerlendirmesi"]
    frame["ömür_öncelik_yorumu"] = comments["ömür_öncelik_yorumu"]
    return frame


def inspection_priority_from_life(values: pd.Series) -> pd.Series:
    life = pd.to_numeric(values, errors="coerce")
    priority = pd.cut(
        life,
        bins=[float("-inf"), 5.0e6, 2.0e7, float("inf")],
        labels=["Immediate Review", "Scheduled Inspection", "Routine Monitoring"],
        right=False,
    ).astype("object")
    priority.loc[life.isna()] = "Not evaluated"
    return priority


def _validate_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive.")


def _numeric_input_or_default(
    data: pd.DataFrame,
    candidate_columns: list[str],
    default_value: float,
) -> pd.Series:
    for column in candidate_columns:
        if column in data.columns:
            values = pd.to_numeric(data[column], errors="coerce")
            return values.fillna(default_value)
    return pd.Series(default_value, index=data.index, dtype="float64")


def _build_engineering_comments(data: pd.DataFrame) -> pd.DataFrame:
    theta_low = _safe_quantile(data["theta_degree"], 1.0 / 3.0)
    theta_high = _safe_quantile(data["theta_degree"], 2.0 / 3.0)
    delta_k_low = _safe_quantile(data["Delta_K_MPa_sqrt_m"], 1.0 / 3.0)
    delta_k_high = _safe_quantile(data["Delta_K_MPa_sqrt_m"], 2.0 / 3.0)
    dadn_low = _safe_quantile(data["da_dN_m_per_cycle"], 1.0 / 3.0)
    dadn_high = _safe_quantile(data["da_dN_m_per_cycle"], 2.0 / 3.0)
    life_low = _safe_quantile(data["Estimated_Life_Cycles"], 0.25)
    life_high = _safe_quantile(data["Estimated_Life_Cycles"], 0.75)

    rows: list[dict[str, str]] = []
    for _, row in data.iterrows():
        risk_class = row.get("risk_class")
        theta_level = _level(row.get("theta_degree"), theta_low, theta_high)
        delta_k_level = _level(row.get("Delta_K_MPa_sqrt_m"), delta_k_low, delta_k_high)
        dadn_level = _level(row.get("da_dN_m_per_cycle"), dadn_low, dadn_high)
        life_level = _inverse_level(row.get("Estimated_Life_Cycles"), life_low, life_high)

        rows.append(
            {
                "yorum_özeti": _comment_summary(risk_class, theta_level, delta_k_level, life_level),
                "geometrik_değerlendirme": _geometry_comment(row, theta_level, row.get("effective_measure_source")),
                "kırılma_mekaniği_değerlendirmesi": _fracture_comment(row, delta_k_level, dadn_level),
                "ömür_öncelik_yorumu": _life_comment(row, theta_level, delta_k_level, life_level),
            }
        )
    return pd.DataFrame(rows, index=data.index)


def _level(value: object, low: float, high: float) -> str:
    if pd.isna(value):
        return "belirsiz"
    value = float(value)
    if value <= low:
        return "düşük"
    if value <= high:
        return "orta"
    return "yüksek"


def _inverse_level(value: object, low: float, high: float) -> str:
    if pd.isna(value):
        return "belirsiz"
    value = float(value)
    if value <= low:
        return "düşük"
    if value <= high:
        return "orta"
    return "yüksek"


def _comment_summary(risk_class: object, theta_level: str, delta_k_level: str, life_level: str) -> str:
    if risk_class == "INCOMPLETE":
        return "Eksik veri"
    if risk_class == "CRITICAL" and delta_k_level == "yüksek":
        return "Yüksek öncelik"
    if delta_k_level == "yüksek":
        return "ΔK yüksek"
    if theta_level == "yüksek":
        return "Açısal sapma yüksek"
    if risk_class == "MEDIUM" or life_level == "orta":
        return "İzlenmeli"
    return "Düşük öncelik"


def _geometry_comment(row: pd.Series, theta_level: str, source: object) -> str:
    source_text = {
        "depth": "Etkin ölçü doğrudan Depth değerinden alınmıştır.",
        "height/2": "Depth bulunmadığı için etkin ölçü Height/2 mühendislik varsayımıyla hesaplanmıştır.",
        "missing": "Depth ve Height bilgisi bulunmadığı için etkin ölçü üretilememiştir.",
    }.get(str(source), "Etkin ölçü kaynağı veri setindeki seçime bağlıdır.")
    return f"Açısal sapma {theta_level} seviyededir. {source_text}"


def _fracture_comment(row: pd.Series, delta_k_level: str, dadn_level: str) -> str:
    delta_k = row.get("Delta_K_MPa_sqrt_m")
    dadn = row.get("da_dN_m_per_cycle")
    if pd.isna(delta_k) or pd.isna(dadn):
        return "Delta K veya da/dN hesaplanamadığı için kırılma mekaniği yorumu sınırlıdır."
    return (
        f"Delta K {delta_k_level} seviyededir ({float(delta_k):.4g} MPa√m). "
        f"Paris Law ile hesaplanan da/dN {dadn_level} seviyededir ({float(dadn):.3E} m/cycle). "
        "Delta K arttıkça Paris Law bağıntısında çatlak ilerleme hızı üstel olarak artar."
    )


def _life_comment(row: pd.Series, theta_level: str, delta_k_level: str, life_level: str) -> str:
    life = row.get("Estimated_Life_Cycles")
    priority = row.get("inspection_priority", "Not evaluated")
    if pd.isna(life):
        return "Estimated life hesaplanamadığı için öncelik yorumu eksik veriyle sınırlıdır."
    if theta_level == "yüksek" and delta_k_level == "düşük":
        return (
            "Bu kusur geometrik olarak belirgin bir wrinkle davranışı göstermektedir; ancak mevcut assumed stress ve çatlak boyutu kabulüne göre "
            f"Delta K görece düşük kalmıştır. Inspection Priority: {priority}."
        )
    if theta_level == "düşük" and delta_k_level == "yüksek":
        return (
            "Açısal sapma düşük görünmesine rağmen Delta K yüksektir. Bu durum assumed stress veya assumed crack kabulü nedeniyle "
            f"kırılma mekaniği açısından dikkat gerektirir. Inspection Priority: {priority}."
        )
    if theta_level == "yüksek" and delta_k_level == "yüksek":
        return (
            "Kusur hem geometrik hem kırılma mekaniği açısından yüksek öncelik göstermektedir. "
            f"Inspection Priority: {priority}."
        )
    if theta_level == "düşük" and delta_k_level == "düşük":
        return f"Kusur mevcut varsayımlar altında düşük öncelikli görünmektedir. Inspection Priority: {priority}."
    return f"Estimated life {float(life):.4g} çevrimdir ve göreceli önceliklendirme için kullanılmalıdır. Inspection Priority: {priority}."


def _safe_quantile(values: pd.Series, quantile: float) -> float:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return float("inf")
    return float(clean.quantile(quantile))


def paris_law_rate(delta_k: float | np.ndarray, c_value: float, m_value: float) -> float | np.ndarray:
    """Calculate da/dN = C * (DeltaK)^m."""

    if c_value <= 0:
        raise ValueError("c_value must be positive.")
    if m_value <= 0:
        raise ValueError("m_value must be positive.")
    return c_value * np.power(delta_k, m_value)


def estimate_remaining_cycles(
    a_initial: float,
    a_critical: float,
    sigma: float,
    c_value: float,
    m_value: float,
    steps: int = 1000,
    geometry_factor: float = 1.12,
    unit_conversion: float = 1000.0,
) -> float:
    """Estimate theoretical cycles, treating crack-size inputs as mm and integrating in m."""

    if a_initial < 0:
        raise ValueError("a_initial must be non-negative.")
    if a_critical <= a_initial:
        return 0.0
    if sigma <= 0:
        raise ValueError("sigma must be positive.")
    if c_value <= 0:
        raise ValueError("c_value must be positive.")
    if m_value <= 0:
        raise ValueError("m_value must be positive.")
    if steps < 10:
        raise ValueError("steps must be at least 10.")
    if geometry_factor <= 0:
        raise ValueError("geometry_factor must be positive.")
    if unit_conversion <= 0:
        raise ValueError("unit_conversion must be positive.")

    a_initial_m = max(a_initial / unit_conversion, 1e-12)
    a_critical_m = a_critical / unit_conversion
    a_grid = np.linspace(a_initial_m, a_critical_m, steps)
    delta_k = geometry_factor * sigma * np.sqrt(math.pi * a_grid)
    rates = paris_law_rate(delta_k, c_value, m_value)

    if np.any(rates <= 0):
        raise ValueError("Paris Law rate must stay positive over the integration range.")

    integrand = 1.0 / rates
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(integrand, a_grid))
    return float(np.trapz(integrand, a_grid))


def add_remaining_cycles(
    data: pd.DataFrame,
    sigma: float,
    c_value: float,
    m_value: float,
    a_initial_column: str = "effective_measure",
    a_critical: float | None = None,
    a_critical_column: str | None = None,
    output_column: str = "remaining_cycles",
    steps: int = 1000,
    geometry_factor: float = 1.12,
    unit_conversion: float = 1000.0,
) -> pd.DataFrame:
    """Add row-wise Paris Law remaining-cycle estimates."""

    if a_critical is None and a_critical_column is None:
        raise ValueError("Provide either a_critical or a_critical_column.")

    frame = data.copy()

    def estimate(row: pd.Series) -> float:
        a_initial = row[a_initial_column]
        critical = row[a_critical_column] if a_critical_column else a_critical
        if pd.isna(a_initial) or pd.isna(critical):
            return np.nan
        try:
            return estimate_remaining_cycles(
                float(a_initial),
                float(critical),
                sigma=sigma,
                c_value=c_value,
                m_value=m_value,
                steps=steps,
                geometry_factor=geometry_factor,
                unit_conversion=unit_conversion,
            )
        except ValueError:
            return np.nan

    frame[output_column] = frame.apply(estimate, axis=1)
    return frame
