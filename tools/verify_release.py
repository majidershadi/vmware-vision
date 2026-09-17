"""Check app contents, versions and UCC output before distribution."""

import ast
import configparser
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import xml.etree.ElementTree as ET


def verify(root, version):
    conf = configparser.ConfigParser(interpolation=None)
    conf.read(root / "default/app.conf")
    assert conf["launcher"]["version"] == conf["id"]["version"] == version
    assert (root / "VERSION").read_text().splitlines() == [version, version]
    manifest = json.loads((root / "app.manifest").read_text())
    assert manifest["info"]["id"]["version"] == version
    assert manifest["info"]["license"]["name"] == "Apache-2.0"
    config = json.loads(
        (root / "appserver/static/js/build/globalConfig.json").read_text()
    )
    assert config["meta"]["version"] == version
    assert config["meta"]["_uccVersion"] == "6.6.0"
    for name in ["transforms.conf", "restmap.conf"]:
        conf = configparser.ConfigParser(interpolation=None)
        conf.read(root / "default" / name)
        for section in conf.values():
            if "python.version" in section:
                assert section["python.version"] == "python3.9"
                assert {v.strip() for v in section["python.required"].split(",")} == {
                    "3.9",
                    "3.13",
                }
    for name in ["vmware_lookup.py", "vmware_vision_parser.py", "vmware_vision_cim.py"]:
        ast.parse((root / "bin" / name).read_text(), feature_version=(3, 9))
    base = (root / "appserver/templates/base.html").read_text()
    assert all(
        marker not in base for marker in ["<%", "${", "cherrypy", "__APP_NAME__"]
    )
    assert "../../config?autoload=1" in base
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        assert not {
            "local",
            ".git",
            ".venv",
            "__pycache__",
            "tests",
            "reports",
            "backups",
        } & set(rel.parts), rel
        assert path.suffix.lower() not in {
            ".pyc",
            ".pyo",
            ".so",
            ".dll",
            ".pyd",
            ".dylib",
            ".key",
            ".pem",
        }, rel
        if path.suffix == ".xml":
            ET.parse(path)
    for name, dimensions in [
        ("appIcon.png", (36, 36)),
        ("appIcon_2x.png", (72, 72)),
        ("appLogo.png", (160, 40)),
        ("appLogo_2x.png", (320, 80)),
    ]:
        import struct

        data = (root / "appserver/static" / name).read_bytes()
        assert data == (root / "static" / name).read_bytes(), name
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert struct.unpack(">II", data[16:24]) == dimensions, name
    print("Release contents verified:", root.name, version)


def main():
    path = Path(sys.argv[1]).resolve()
    version = sys.argv[2]
    if path.is_dir():
        verify(path, version)
        return
    with tempfile.TemporaryDirectory(prefix="vmware-vision-verify-") as temp:
        with tarfile.open(path) as archive:
            for member in archive.getmembers():
                parts = Path(member.name).parts
                assert parts and parts[0] == "vmware_vision" and ".." not in parts
                assert not member.issym() and not member.islnk()
                assert not member.name.startswith("/")
            archive.extractall(temp, filter="data")
        verify(Path(temp) / "vmware_vision", version)


if __name__ == "__main__":
    main()
