"""Portable CSV/JSON/Markdown/PNG reports with no hidden validation claims."""

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .core import Calibration, metrics, predict


def export_report(data: pd.DataFrame, calibration: Calibration, directory: str | Path) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    predicted = predict(data, calibration)
    predicted.to_csv(directory / "predictions.csv", index=False)
    records: list[dict[str, Any]] = []
    for split, group in predicted.groupby("split"):
        for kind, target in (("thermal", "nu_ref"), ("hydraulic", "f_ref")):
            records.append(
                dict(
                    split=split,
                    model=kind,
                    **metrics(group[target].to_numpy(), group[f"{kind}_prediction"].to_numpy()),
                )
            )
    summary = pd.DataFrame(records)
    summary.to_csv(directory / "metrics.csv", index=False)
    grouped = []
    for dimension, bins in (
        ("re", [0, 200, 1000, 2000, 5000, np.inf]),
        ("temperature_c", [-np.inf, 0, 20, 40, 60, 80, np.inf]),
    ):
        for split, split_data in predicted.groupby("split"):
            for interval, group in split_data.groupby(
                pd.cut(split_data[dimension], bins), observed=True
            ):
                for kind, target in (("thermal", "nu_ref"), ("hydraulic", "f_ref")):
                    grouped.append(
                        dict(
                            dimension=dimension,
                            interval=str(interval),
                            split=split,
                            model=kind,
                            **metrics(
                                group[target].to_numpy(), group[f"{kind}_prediction"].to_numpy()
                            ),
                        )
                    )
    pd.DataFrame(grouped).to_csv(directory / "range_metrics.csv", index=False)
    payload = {
        "schema_version": 1,
        "calibration": calibration.to_dict(),
        "platehx_correction": calibration.platehx_correction(),
        "provenance": sorted(predicted.provenance.unique().tolist()),
        "extrapolated_rows": int(predicted.outside_training_domain.sum()),
        "metrics": records,
    }
    (directory / "calibration.json").write_text(
        json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8"
    )
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    for row, (kind, target, unit) in enumerate(
        (("thermal", "nu_ref", "Nu [-]"), ("hydraulic", "f_ref", "Darcy f [-]"))
    ):
        for split, group in predicted.groupby("split"):
            axes[row, 0].scatter(group[target], group[f"{kind}_prediction"], label=split, s=18)
            axes[row, 1].scatter(group.re, group[f"{kind}_error_pct"], label=split, s=18)
            axes[row, 2].scatter(group.temperature_c, group[f"{kind}_error_pct"], label=split, s=18)
        lo, hi = predicted[target].min(), predicted[target].max()
        axes[row, 0].plot([lo, hi], [lo, hi], "k--", lw=1)
        axes[row, 0].set(xlabel=f"Reference {unit}", ylabel=f"Predicted {unit}")
        axes[row, 1].set(xlabel="Re [-]", ylabel="Error [%]", xscale="log")
        axes[row, 2].set(xlabel="Bulk temperature [C]", ylabel="Error [%]")
        for axis in axes[row]:
            axis.legend()
            axis.grid(alpha=0.2)
    fig.suptitle("Engineering model calibration | " + ", ".join(payload["provenance"]))
    fig.savefig(directory / "comparison.png", dpi=150)
    plt.close(fig)
    md = (
        "# Calibration report\n\nProvenance: "
        + ", ".join(payload["provenance"])
        + "\n\nIndependent split labels were provided by the data author. Only train rows entered fitting.\n\n"
        + "```\n"
        + summary.to_string(index=False)
        + "\n```\n\n"
        + f"Rows outside training Re/temperature rectangle: {payload['extrapolated_rows']}.\n\n"
        + "![Comparison and residuals](comparison.png)\n\n"
        + "See range_metrics.csv for Reynolds and temperature bands. Synthetic recovery is an algorithm test, "
        + "not experimental or manufacturer validation. Repeated conditions/specimens must be grouped before splitting. "
        + "The fit does not estimate measurement uncertainty or establish safety margins.\n"
    )
    (directory / "REPORT.md").write_text(md, encoding="utf-8")
    return directory
