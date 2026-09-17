"""Regression coverage for the Splunk 10.0.2 interpreter configuration."""

import ast
import configparser
import re
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from additional_packaging import compatible_python


class RuntimeCompatibility(unittest.TestCase):
    def test_global_automatic_lookup_has_visible_script(self):
        # Splunk metadata permits an unnamed stanza, unlike ConfigParser.
        text = (ROOT / "package/metadata/default.meta").read_text(encoding="utf-8")
        config = configparser.ConfigParser()
        config.read_string(re.sub(r"^\[\]$", "[app_defaults]", text, flags=re.M))
        props = configparser.ConfigParser(interpolation=None)
        props.read(ROOT / "package/default/props.conf")
        transforms = configparser.ConfigParser(interpolation=None)
        transforms.read(ROOT / "package/default/transforms.conf")
        self.assertEqual(config["props"]["export"], "system")
        self.assertEqual(config["transforms"]["export"], "system")
        for stanza in props.values():
            for key, value in stanza.items():
                if key.startswith("lookup-"):
                    command = transforms[value.split()[0]]["external_cmd"].split()[0]
                    self.assertTrue((ROOT / "package/bin" / command).is_file())
                    acl = config["searchscripts/" + command]
                    self.assertEqual(acl["export"], "system")
                    self.assertEqual(
                        acl["access"], "read : [ * ], write : [ admin, sc_admin ]"
                    )
        self.assertEqual(config["app_defaults"]["export"], "none")
        self.assertNotIn("searchscripts", config)  # Do not export every UCC script.

    def test_legacy_runtime_settings_preserve_other_stanzas(self):
        source = "[lookup]\nexternal_cmd = vmware_lookup.py\npython.version = python3\npython.required = 3.9, 3.13\n\n[other]\nvalue = keep\n"
        normalized = compatible_python(source)
        config = configparser.ConfigParser()
        config.read_string(normalized)
        self.assertEqual(config["lookup"]["python.version"], "python3.9")
        self.assertEqual(config["lookup"]["python.required"], "3.9, 3.13")
        self.assertEqual(config["lookup"]["external_cmd"], "vmware_lookup.py")
        self.assertEqual(config["other"]["value"], "keep")
        self.assertEqual(normalized, compatible_python(normalized))

    def test_lookup_configuration_and_python39_syntax(self):
        config = configparser.ConfigParser()
        config.read(ROOT / "package/default/transforms.conf")
        self.assertEqual(
            config["vmware_vision_normalize"]["python.version"], "python3.9"
        )
        self.assertEqual(
            config["vmware_vision_normalize"]["python.required"], "3.9, 3.13"
        )
        for name in (
            "vmware_lookup.py",
            "vmware_vision_parser.py",
            "vmware_vision_cim.py",
        ):
            ast.parse(
                (ROOT / "package/bin" / name).read_text(encoding="utf-8"),
                feature_version=(3, 9),
            )
