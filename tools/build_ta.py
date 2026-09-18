"""Build the ingestion-only TA from the main app's parsing settings.

Uses only the Python standard library and never contacts a Splunk instance.
The explicit file list excludes local configuration, credentials and build tools.
"""

import configparser
import gzip
import hashlib
import io
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
APP_ID = "TA-vmware-vision"
VERSION = "1.0.1"
SOURCETYPES = (
    "vmware:vision:vcenter",
    "vmware:vision:aria",
    "vmware:vision:esxi",
    "vmware:vision:json",
)
PARSING_KEYS = (
    "SHOULD_LINEMERGE",
    "LINE_BREAKER",
    "TRUNCATE",
    "MAX_TIMESTAMP_LOOKAHEAD",
    "TIME_PREFIX",
    "CHARSET",
)


def payload(root=ROOT):
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    config.read(root / "package/default/props.conf", encoding="utf-8")
    sections = []
    for sourcetype in SOURCETYPES:
        sections.append(
            "["
            + sourcetype
            + "]\n"
            + "\n".join(key + " = " + config[sourcetype][key] for key in PARSING_KEYS)
        )
    files = {
        "default/props.conf": "# Raw parsing settings shared with the search app.\n\n"
        + "\n\n".join(sections)
        + "\n",
        "default/app.conf": """[install]
is_configured = 0
build = 101
state = enabled

[ui]
is_visible = 0
label = VMware Vision Ingestion Add-on

[launcher]
author = Majid Ershadi
description = VMware syslog event boundaries, timestamps and character encoding for parsing tiers
version = 1.0.1

[id]
name = TA-vmware-vision
version = 1.0.1

[package]
id = TA-vmware-vision
check_for_updates = true
""",
        "metadata/default.meta": """[]
access = read : [ * ], write : [ admin, sc_admin ]
export = none

[props]
export = system
""",
        "README.txt": """TA-vmware-vision 1.0.1
VMware Vision ingestion add-on for Splunk heavy forwarders and indexers.

Install on the first full parsing tier for each VMware input path. If an HF
already parses all VMware events, downstream indexers do not need another
copy for parsing. Keep the full vmware_vision app on the search head.

This TA handles event boundaries, timestamps and character encoding only.
VM field extraction remains a search-time function of the main app and its
distributed-search knowledge bundle. The TA has no Python runtime dependency.

No inputs, outputs, indexes, credentials, dashboards or scripts are enabled
or included as active configuration. README/examples contains inactive samples.
Select only the examples needed on each tier and edit them before use.

Read README/DEPLOYMENT.md for deployment and acceptance steps.
Verify collection and distributed search in your deployment.
Compatible with VMware Vision for Splunk 1.1.0.
""",
    }
    files["LICENSES/LICENSE.txt"] = (root / "package/LICENSES/LICENSE.txt").read_text(
        encoding="utf-8"
    )
    files["README/DEPLOYMENT.md"] = (root / "docs/DEPLOYMENT.md").read_text(
        encoding="utf-8"
    )
    for name in (
        "inputs-hf.conf.example",
        "indexes-indexer.conf.example",
        "indexes-cluster.conf.example",
    ):
        files["README/examples/" + name] = (root / "docs/ta-examples" / name).read_text(
            encoding="utf-8"
        )
    content = {
        name: text.replace("\r\n", "\n").encode("utf-8") for name, text in files.items()
    }
    for name in ("appIcon.png", "appIcon_2x.png"):
        content["static/" + name] = (root / "package/static" / name).read_bytes()
    return content


def archive(files):
    """Produce a reproducible Linux-compatible package on any build platform."""
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buffer, mtime=0) as compressed:
        with tarfile.open(
            fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT
        ) as stream:
            directories = {APP_ID}
            for name in files:
                parent = Path(name).parent
                while parent != Path("."):
                    directories.add(APP_ID + "/" + parent.as_posix())
                    parent = parent.parent
            for name in sorted(directories):
                info = tarfile.TarInfo(name + "/")
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                stream.addfile(info)
            for name, content in sorted(files.items()):
                info = tarfile.TarInfo(APP_ID + "/" + name)
                info.size = len(content)
                info.mode = 0o644
                stream.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def main():
    files = payload()
    for name, content in files.items():
        target = ROOT / APP_ID / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    destination = ROOT / "dist" / f"{APP_ID}-{VERSION}.tar.gz"
    destination.parent.mkdir(exist_ok=True)
    package = archive(files)
    destination.write_bytes(package)
    checksum = hashlib.sha256(package).hexdigest()
    destination.with_name(destination.name + ".sha256").write_text(
        checksum + "  " + destination.name + "\n", encoding="utf-8"
    )
    print(destination)
    print(checksum)


if __name__ == "__main__":
    main()
