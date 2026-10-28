"""Synthetic algorithm test ONLY. Fixed truth and independent seeded noise, no manufacturer data."""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(20261028)
rows = []
for i in range(120):
    # Interleaved fixed split; exact boundary points are training points.
    re = float(np.geomspace(220, 9000, 120)[i])
    temperature = float(rng.uniform(20, 80))
    nu = 0.2 * re**0.65 * 4.0 ** (1 / 3)
    friction = 3.0 * re**-0.15
    rows.append(
        {
            "case_id": f"synthetic-{i:03}",
            "split": "validation" if i % 4 == 1 else "train",
            "provenance": "synthetic: power-law baseline with known corrections and 1% Gaussian noise",
            "re": re,
            "temperature_c": temperature,
            "nu_base": nu,
            "f_base": friction,
            "nu_ref": nu * 1.18 * (re / 1000) ** 0.07 * (1 + rng.normal(0, 0.01)),
            "f_ref": friction * 0.86 * (re / 1000) ** -0.04 * (1 + rng.normal(0, 0.01)),
        }
    )
Path("data").mkdir(exist_ok=True)
data = pd.DataFrame(rows)
data.to_csv("data/synthetic.csv", index=False)
data.to_excel("data/synthetic.xlsx", index=False)
print("Wrote 120 SYNTHETIC cases; truth thermal=(1.18,0.07), hydraulic=(0.86,-0.04)")
