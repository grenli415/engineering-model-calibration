"""Small repository secret hygiene check; not a substitute for hosted secret scanning."""

import re
from pathlib import Path

patterns = [
    re.compile(r"github" + r"_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gh[pousr]" + r"_[A-Za-z0-9]{30,}"),
    re.compile(r"-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
bad = []
for path in Path(".").rglob("*"):
    if not path.is_file() or any(
        part in {".git", ".venv", "dist", "build", "__pycache__", ".pytest_cache", ".ruff_cache"}
        for part in path.parts
    ):
        continue
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    if any(pattern.search(content) for pattern in patterns):
        bad.append(str(path))
if bad:
    raise SystemExit("Possible secrets in: " + ", ".join(bad))
print("No supported token/private-key patterns found in project text files")
