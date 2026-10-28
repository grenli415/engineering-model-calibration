# Verification record

Date: 2026-10-28. Windows, Python 3.12.2. Companion platehx installed in the same environment.

* `python -m pytest -q`: **14 passed**. Repeated after formatting: 14 passed in 12.22 s.
* Tests include noiseless truth recovery for all four coefficients, held-out-target independence,
  manually checked metric arithmetic, CSV/Excel round trips, malformed inputs, report files,
  range summaries, extrapolation flags and an actual coupled platehx calculation.
* CLI executed successfully on the 120-row seeded synthetic dataset and exported CSV/JSON/PNG/Markdown.
* Companion integration example executed; computed corrected duty: 162213.496 W.
  This is synthetic-coefficient API verification, not a validated equipment prediction.
* Ruff check/format check passed. Wheel/sdist built. `pip check` found no broken requirements.
* Pattern secret scan passed; detector scope is documented in the calculator's verification record.

Synthetic demonstration: 90 train / 30 validation observations, seed 20261028, 1% Gaussian noise.

| Model / split | MAE | RMSE | MAPE % | Max absolute error |
|---|---:|---:|---:|---:|
| Thermal / validation | 0.406767 | 0.588850 | 0.726705 | 1.948458 |
| Hydraulic / validation | 0.006563 | 0.008072 | 0.730204 | 0.020354 |

All target errors except MAPE are dimensionless Nu or Darcy-f units. Full unrounded output
is in example-report/metrics.csv. Actual plots were visually inspected for labels and split legends.

Runtime versions: NumPy 2.5.4, SciPy 1.18.1, pandas 3.1.0, Matplotlib 3.11.2,
openpyxl 3.1.5. The CI verifies standalone operation plus a separate explicit companion test.
See GitHub Actions for the actual hosted run conclusion. No independent experimental or
manufacturer dataset is included, and no industrial validation accuracy is claimed.

The v0.1.1 wheel was installed in a separate clean environment. CSV calibration and Excel CLI
report export executed successfully; preserved upstream license is included in the wheel.
