"""Keep native AppInspect reports and stop on current or future failures."""

import json
from pathlib import Path
import subprocess
import sys

inspector = sys.argv[1]
failed = False
for filename in sys.argv[2:]:
    archive = Path(filename)
    report = archive.with_name(
        "appinspect-" + archive.name.removesuffix(".tar.gz") + ".json"
    )
    result = subprocess.run(
        [
            inspector,
            "inspect",
            str(archive),
            "--mode",
            "precert",
            "--included-tags",
            "cloud",
            "--included-tags",
            "self-service",
            "--output-file",
            str(report),
        ]
    )
    report.with_suffix(".exit-code").write_text(str(result.returncode) + "\n")
    if not report.exists():
        raise SystemExit("AppInspect did not produce a report: " + str(archive))
    summary = json.loads(report.read_text())["summary"]
    print(archive.name, summary)
    if any(summary.get(key, 0) for key in ["error", "failure", "future_failure"]):
        failed = True
    elif result.returncode not in (0, 1):
        failed = True
if failed:
    raise SystemExit("Release checks failed. Review the AppInspect reports.")
