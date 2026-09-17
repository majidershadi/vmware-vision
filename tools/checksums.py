"""Write checksums for the two installation packages."""

import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
archives = sorted((root / "dist").glob("*.tar.gz"))
lines = [
    hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.name
    for path in archives
]
(root / "dist/SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
