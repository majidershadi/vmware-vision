"""Check source version and runtime declarations before a UCC build."""

import configparser
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
version = sys.argv[1]
sys.path.insert(0, str(root / "package/bin"))
from vmware_vision_parser import VERSION, OUTPUT_FIELDS

config = json.loads((root / "globalConfig.json").read_text())
manifest = json.loads((root / "package/app.manifest").read_text())
assert (
    VERSION == config["meta"]["version"] == manifest["info"]["id"]["version"] == version
)
assert set(config["meta"]["supportedPythonVersion"]) == {"3.9", "3.13"}
assert (
    config["meta"].get("checkForUpdates", True) is True
), "Splunkbase update checks must remain enabled"
app = configparser.ConfigParser(interpolation=None)
app.read(root / "package/default/app.conf")
assert app.getboolean(
    "package", "check_for_updates", fallback=True
), "Splunkbase update checks must remain enabled"
props = configparser.ConfigParser(interpolation=None)
props.read(root / "package/default/props.conf")
for stanza in props.sections():
    outputs = props[stanza]["LOOKUP-vmware_vision"].split(" OUTPUT ", 1)[1].split()
    assert outputs == OUTPUT_FIELDS, "Lookup output list differs: " + stanza
assert not (root / "package/local").exists(), "Local configuration must not be packaged"
print("Source configuration verified")
