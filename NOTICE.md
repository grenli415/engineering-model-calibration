# Provenance and third-party notices

Audit date: 2026-10-28. Inspiration/reference repository: https://github.com/alphabench/aeroid
Reviewed revision: `3c876ee2068a672536b16abb009cce8c2c55052f`; full locally cloned default-branch ancestry: 36 commits.
See docs/UPSTREAM_HISTORY.txt for the observed history, including authors and timestamps.
The upstream LICENSE is MIT and permits reuse with retention of copyright and permission notices.
The verbatim license is retained in third_party/upstream-aeroid-LICENSE.txt.

This is a new independent implementation, not a renamed upstream checkout. Upstream source,
tests, datasets and Git commits are not copied into the product. Code was reviewed for architecture
and scope. Public Git history can show recorded contributors and changes; it cannot prove
ownership of every line, absence of unrecorded sources, or the validity of all third-party rights.
No claim of an exhaustive legal clearance is made.

AeroID's relevant architectural ideas are named observations, separate estimation and
validation, solver diagnostics, and synthetic truth-recovery tests. This project targets steady
thermal/hydraulic algebraic models, CSV/Excel references, relative-residual least squares and
engineering reports. No ODE, aerospace adapters, Kalman filters or Bayesian code was reused.

Runtime dependencies: NumPy, SciPy, pandas and Matplotlib (BSD-style licenses), openpyxl (MIT).
Their license notices are distributed with the packages; these algorithms are not claimed as
original numerical optimization methods. The optional companion platehx project has its own
dependency and correlation notices.
