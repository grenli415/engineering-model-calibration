"""Command-line calibration and report export."""

import argparse

from .core import calibrate, load_data
from .report import export_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibrate Nu and Darcy friction from CSV/XLSX")
    parser.add_argument("input")
    parser.add_argument("--output", default="report")
    args = parser.parse_args()
    try:
        data = load_data(args.input)
        export_report(data, calibrate(data), args.output)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Calibration failed: {exc}\n")
    print(f"Report exported to {args.output}")


if __name__ == "__main__":
    main()
