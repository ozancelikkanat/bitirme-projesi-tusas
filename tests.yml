"""Small built-in dataset for demos and smoke tests."""

from __future__ import annotations

import pandas as pd


def make_sample_dataframe() -> pd.DataFrame:
    """Return representative wrinkle records with mixed depth/height availability."""

    return pd.DataFrame(
        [
            {"defect_id": "W-001", "length": 42.0, "width": 10.0, "depth": 0.10, "height": None},
            {"defect_id": "W-002", "length": 30.0, "width": 5.0, "depth": None, "height": 0.40},
            {"defect_id": "W-003", "length": 55.0, "width": 5.0, "depth": 0.50, "height": None},
            {"defect_id": "W-004", "length": 18.0, "width": 5.0, "depth": 1.00, "height": None},
            {"defect_id": "W-005", "length": 60.0, "width": 8.0, "depth": None, "height": None},
            {"defect_id": "W-006", "length": 25.0, "width": 0.0, "depth": 0.15, "height": None},
        ]
    )
