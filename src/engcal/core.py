"""Bounded nonlinear least squares for independent thermal and hydraulic models."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.optimize import least_squares

FloatArray = NDArray[np.float64]
REQUIRED = (
    "case_id",
    "split",
    "provenance",
    "re",
    "temperature_c",
    "nu_base",
    "nu_ref",
    "f_base",
    "f_ref",
)


def validate(data: pd.DataFrame) -> pd.DataFrame:
    """Check schema, finite SI values, positive dimensionless targets and unique case IDs."""
    missing = set(REQUIRED) - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if data.empty or data[list(REQUIRED)].isna().any().any():
        raise ValueError("Data must be nonempty with no missing required values")
    if data.case_id.duplicated().any():
        raise ValueError("Duplicate case IDs: split leakage or duplicate observations")
    if not set(data.split).issubset({"train", "validation"}):
        raise ValueError("split must be train or validation")
    if data.provenance.astype(str).str.strip().eq("").any():
        raise ValueError("Every row needs provenance, e.g. synthetic")
    result = data.copy()
    for name in REQUIRED[3:]:
        result[name] = pd.to_numeric(result[name], errors="raise")
        if not np.isfinite(result[name]).all():
            raise ValueError(f"Nonfinite {name}")
        if name != "temperature_c" and (result[name] <= 0).any():
            raise ValueError(f"{name} must be positive")
    return result


def load_data(path: str | Path) -> pd.DataFrame:
    """Import CSV or first worksheet of .xlsx with strict validation."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return validate(pd.read_csv(path))
    if path.suffix.lower() == ".xlsx":
        return validate(pd.read_excel(path, engine="openpyxl"))
    raise ValueError("Supported formats: .csv and .xlsx")


def metrics(reference: FloatArray, prediction: FloatArray) -> dict[str, Any]:
    """MAE, RMSE and max absolute error in target units; MAPE in percent.

    MAPE is undefined for zero reference values: report None and a count, never silently drop rows.
    """
    a, b = np.asarray(reference, dtype=float), np.asarray(prediction, dtype=float)
    if a.ndim != 1 or a.size == 0 or a.shape != b.shape or not np.isfinite([a, b]).all():
        raise ValueError("Equal, nonempty finite 1-D arrays required")
    error = b - a
    zeros = int(np.count_nonzero(a == 0))
    return {
        "n": int(a.size),
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mape_pct": None if zeros else float(100 * np.mean(np.abs(error / a))),
        "max_abs_error": float(np.max(np.abs(error))),
        "zero_reference_count": zeros,
    }


@dataclass(frozen=True)
class Fit:
    scale: float
    exponent: float
    jacobian_rank: int
    condition_number: float
    nfev: int
    cost: float
    at_bound: bool


@dataclass(frozen=True)
class Calibration:
    thermal: Fit
    hydraulic: Fit
    re_min: float
    re_max: float
    temperature_min_c: float
    temperature_max_c: float
    training_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def platehx_correction(self) -> dict[str, float]:
        """Keyword arguments accepted by platehx.model.Correction."""
        return {
            "thermal_scale": self.thermal.scale,
            "thermal_exponent": self.thermal.exponent,
            "hydraulic_scale": self.hydraulic.scale,
            "hydraulic_exponent": self.hydraulic.exponent,
            "re_min": self.re_min,
            "re_max": self.re_max,
        }


def _fit(data: pd.DataFrame, base: str, target: str) -> Fit:
    re = data.re.to_numpy(dtype=float)
    b, y = data[base].to_numpy(dtype=float), data[target].to_numpy(dtype=float)

    def residual(theta: FloatArray) -> FloatArray:
        # Relative residuals balance the influence of small/large targets.
        return (b * theta[0] * (re / 1000) ** theta[1] - y) / y

    result = least_squares(
        residual,
        x0=[1.0, 0.0],
        bounds=([0.05, -1.0], [20.0, 1.0]),
        method="trf",
        x_scale="jac",
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
        max_nfev=2000,
    )
    if not result.success or not np.isfinite(result.x).all():
        raise ValueError(f"Optimization failed: {result.message}")
    singular = np.linalg.svd(result.jac, compute_uv=False)
    rank = int(np.linalg.matrix_rank(result.jac))
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0 else float("inf")
    if rank < 2 or condition > 1e8:
        raise ValueError("Coefficients are unidentifiable; vary Reynolds in training data")
    return Fit(
        float(result.x[0]),
        float(result.x[1]),
        rank,
        condition,
        int(result.nfev),
        float(result.cost),
        bool(np.any(result.active_mask)),
    )


def calibrate(data: pd.DataFrame) -> Calibration:
    data = validate(data)
    train = data[data.split == "train"]
    if len(train) < 4 or train.re.nunique() < 3:
        raise ValueError("At least four training rows at three distinct Reynolds numbers required")
    if not (data.split == "validation").any():
        raise ValueError("A separate validation split is required")
    return Calibration(
        _fit(train, "nu_base", "nu_ref"),
        _fit(train, "f_base", "f_ref"),
        float(train.re.min()),
        float(train.re.max()),
        float(train.temperature_c.min()),
        float(train.temperature_c.max()),
        tuple(train.case_id.astype(str)),
    )


def predict(data: pd.DataFrame, calibration: Calibration) -> pd.DataFrame:
    result = validate(data)
    for kind, base, target in (("thermal", "nu_base", "nu_ref"), ("hydraulic", "f_base", "f_ref")):
        fit = getattr(calibration, kind)
        pred = result[base] * fit.scale * (result.re / 1000) ** fit.exponent
        result[f"{kind}_prediction"] = pred
        result[f"{kind}_error"] = pred - result[target]
        result[f"{kind}_error_pct"] = 100 * (pred - result[target]) / result[target]
    result["outside_training_domain"] = ~result.re.between(
        calibration.re_min, calibration.re_max
    ) | ~result.temperature_c.between(calibration.temperature_min_c, calibration.temperature_max_c)
    return result
