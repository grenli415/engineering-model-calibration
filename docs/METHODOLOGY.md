# Calibration methodology and limitations

Checked 2026-10-28. This repository fits algebraic thermal and hydraulic correction models,
inspired by AeroID's separation of data, identification and validation. It does not republish
AeroID's flight dynamics, ODE estimators, filters or Bayesian inference.

## Required data schema

| Column | Meaning |
|---|---|
| case_id | Unique observation ID, no duplicates across train/validation |
| split | train or validation, provided before optimization |
| provenance | Origin of each observation; synthetic data must say synthetic |
| re | Reynolds number [-], >0 |
| temperature_c | Bulk temperature [C] |
| nu_base, nu_ref | Baseline and reference Nusselt numbers [-], >0 |
| f_base, f_ref | Baseline and reference **Darcy** friction factors [-], >0 |

CSV and .xlsx first worksheet are supported. Headers and units must match exactly. Data with
missing, nonfinite, duplicate or nonpositive targets are rejected. References must be derived
from independent measurements or trusted reference calculations; predicted values exported
from platehx alone do not supply a valid reference. Deriving individual film coefficients from
overall measured U is an inverse problem requiring additional assumptions or experiments.
For friction, subtract known port/elevation losses before deriving channel Darcy f.

## Objective and optimizer

Thermal: Nu_pred=Nu_base a_T(Re/1000)^b_T.
Hydraulic: f_pred=f_base a_H(Re/1000)^b_H.
Both models use scipy.optimize.least_squares (TRF) with relative residual
r_i=(y_pred-y_ref)/y_ref. Minimize 1/2 sum r_i². Scale a in [0.05,20], exponent b in [-1,1].
These are configurable only in source for this version; bounds are engineering guardrails,
not physical proof. The two fits are independent; no target from the other channel is used.
Finite-difference Jacobian, tight convergence tolerances, max 2000 function evaluations.
Convergence status, function evaluations, cost, active bounds, Jacobian rank and condition number
are exported. Rank deficiency / condition >1e8 is rejected. At least four training observations
at three distinct Reynolds numbers are required. At-bound estimates must be reviewed.

Reference: [SciPy least_squares official documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
Trust region method: Branch, Coleman & Li (1999), *A Subspace, Interior, and Conjugate Gradient
Method for Large-Scale Bound-Constrained Minimization Problems*, SIAM J. Sci. Comput. 21(1), 1–23,
[DOI 10.1137/S1064827595289108](https://doi.org/10.1137/S1064827595289108).

## Validation and metrics

Only train rows enter optimization. Validation rows are evaluated afterwards; tests prove that
changing held-out targets cannot change the fit. User-supplied split labels do not guarantee
statistical independence: group repeated conditions, runs and specimens before splitting. The
software catches duplicate IDs, not all possible experimental leakage.

For error e=prediction-reference:
MAE=mean(|e|), RMSE=sqrt(mean(e²)), maximum error=max(|e|), MAPE=100 mean(|e/reference|).
MAE/RMSE/max use target units, here dimensionless Nu or Darcy f. MAPE is percent. The standalone
metric function reports MAPE=null with a count if any reference equals zero; calibration itself
rejects zero targets because the relative residual is undefined.

Reports separate train/validation and thermal/hydraulic models, and aggregate by fixed Reynolds
and temperature intervals with sample counts. Predictions outside the training Re/temperature
rectangle are flagged, not silently presented as interpolation. The rectangle does not guarantee
local data density. Plots show parity and residuals versus Re and bulk temperature.

Exports: JSON coefficients and diagnostics, CSV row predictions and range metrics, Markdown
report and PNG comparison figure. The companion platehx API consumes the correction fields.
Do not transfer coefficients between fluids, plate geometries, correlation variants or equipment
without evidence. The synthetic dataset is a power-law recovery exercise; it is not derived from
manufacturer data and does not validate the plate exchanger physics.

This release does not estimate parameter covariance/confidence intervals, measurement uncertainty,
errors-in-variables, model discrepancy, uncertainty propagation or equipment safety margins.
Temperature is a diagnostic variable, not an additional fitted temperature correction term.
