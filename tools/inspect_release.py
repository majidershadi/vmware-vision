"""Keep native AppInspect reports and stop on current or future failures."""

import json
import configparser
from pathlib import Path
import subprocess
import sys
import tarfile

inspector = sys.argv[1]
failed = False
for filename in sys.argv[2:]:
    archive = Path(filename)
    with tarfile.open(archive) as package:
        configs = [
            member
            for member in package.getmembers()
            if member.isfile()
            and len(Path(member.name).parts) == 3
            and member.name.endswith("/default/app.conf")
        ]
        if len(configs) != 1:
            raise SystemExit(
                "Package must contain exactly one top-level app default/app.conf: "
                + str(archive)
            )
        config = configparser.ConfigParser(interpolation=None)
        config.read_string(package.extractfile(configs[0]).read().decode("utf-8"))
        if not config.getboolean("package", "check_for_updates", fallback=True):
            raise SystemExit(
                "Splunkbase rejects check_for_updates=false: " + str(archive)
            )
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
