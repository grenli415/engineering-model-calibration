import json

import numpy as np
import pandas as pd
import pytest

from engcal import calibrate, export_report, load_data, metrics, predict
from engcal.core import validate


@pytest.fixture
def data():
    re = np.geomspace(220, 9000, 40)
    base_nu = 0.2 * re**0.65
    base_f = 3 * re**-0.15
    return pd.DataFrame(
        {
            "case_id": [f"id{i}" for i in range(40)],
            "split": ["validation" if i % 4 == 1 else "train" for i in range(40)],
            "provenance": "synthetic noiseless recovery test",
            "re": re,
            "temperature_c": np.linspace(20, 80, 40),
            "nu_base": base_nu,
            "f_base": base_f,
            "nu_ref": base_nu * 1.18 * (re / 1000) ** 0.07,
            "f_ref": base_f * 0.86 * (re / 1000) ** -0.04,
        }
    )


def test_exact_recovery_and_holdout(data):
    c = calibrate(data)
    assert c.thermal.scale == pytest.approx(1.18, abs=1e-8)
    assert c.thermal.exponent == pytest.approx(0.07, abs=1e-8)
    assert c.hydraulic.scale == pytest.approx(0.86, abs=1e-8)
    assert c.hydraulic.exponent == pytest.approx(-0.04, abs=1e-8)
    p = predict(data, c)
    validation = p[p.split == "validation"]
    assert np.abs(validation.thermal_error).max() < 1e-7
    # Changing held-out targets cannot change fitted coefficients.
    changed = data.copy()
    changed.loc[changed.split == "validation", "nu_ref"] *= 2
    assert calibrate(changed) == c


def test_metrics_hand_calculation():
    m = metrics(np.array([2.0, 4.0]), np.array([3.0, 2.0]))
    assert m["mae"] == 1.5
    assert m["rmse"] == pytest.approx(np.sqrt(2.5))
    assert m["mape_pct"] == 50
    assert m["max_abs_error"] == 2
    assert metrics(np.array([0.0, 2.0]), np.array([1.0, 2.0]))["mape_pct"] is None


@pytest.mark.parametrize("extension", ["csv", "xlsx"])
def test_import(data, tmp_path, extension):
    path = tmp_path / f"data.{extension}"
    if extension == "csv":
        data.to_csv(path, index=False)
    else:
        data.to_excel(path, index=False)
    pd.testing.assert_frame_equal(load_data(path), data, check_exact=False)


@pytest.mark.parametrize("fault", ["nan", "negative", "duplicate", "missing", "split", "infinity"])
def test_bad_data(data, fault):
    if fault == "nan":
        data.loc[0, "nu_ref"] = np.nan
    elif fault == "negative":
        data.loc[0, "re"] = -2
    elif fault == "duplicate":
        data.loc[0, "case_id"] = data.loc[1, "case_id"]
    elif fault == "missing":
        data = data.drop(columns="f_ref")
    elif fault == "split":
        data.loc[0, "split"] = "test"
    else:
        data.loc[0, "re"] = np.inf
    with pytest.raises(ValueError):
        validate(data)


def test_unidentifiable(data):
    data["re"] = 1000
    with pytest.raises(ValueError):
        calibrate(data)


def test_export(data, tmp_path):
    export_report(data, calibrate(data), tmp_path)
    assert (tmp_path / "comparison.png").stat().st_size > 10000
    payload = json.loads((tmp_path / "calibration.json").read_text())
    assert payload["provenance"] == ["synthetic noiseless recovery test"]
    assert payload["schema_version"] == 1
    ranges = pd.read_csv(tmp_path / "range_metrics.csv")
    assert set(ranges.dimension) == {"re", "temperature_c"}
    assert set(ranges.split) == {"train", "validation"}


def test_extrapolation_flag(data):
    c = calibrate(data)
    data.loc[0, "re"] = 100000
    assert predict(data, c).loc[0, "outside_training_domain"]


def test_companion_integration(data):
    pytest.importorskip("platehx")
    from platehx import Geometry, Stream, rate
    from platehx.model import Correction

    c = calibrate(data)
    result = rate(
        Geometry(),
        21,
        Stream(80, 1),
        Stream(20, 1),
        correction=Correction(**c.platehx_correction()),
    )
    assert result["duty_w"] > 0
