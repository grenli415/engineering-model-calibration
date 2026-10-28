"""Apply fitted dimensionless corrections to the companion exchanger model."""

import json
from pathlib import Path

from platehx import Geometry, Stream, rate
from platehx.model import Correction

payload = json.loads(Path("example-report/calibration.json").read_text())
correction = Correction(**payload["platehx_correction"])
# Demonstrates API interoperability only: synthetic coefficients are NOT equipment validation.
result = rate(Geometry(), 21, Stream(80, 1), Stream(20, 1), correction=correction)
print("SYNTHETIC calibration applied; computed duty [W]:", result["duty_w"])
