"""Offline checks for ingestion separation and portable release packaging."""

import configparser
import io
from pathlib import Path
import re
import sys
import tarfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_ta import APP_ID, archive, payload


def conf(raw):
    result = configparser.ConfigParser(interpolation=None)
    result.optionxform = str
    result.read_string(raw.decode("utf-8"))
    return result


class IngestionPackageTests(unittest.TestCase):
    def test_no_search_runtime_or_active_environment_configuration(self):
        files = payload()
        active = {name for name in files if name.startswith(("default/", "local/"))}
        self.assertEqual(active, {"default/app.conf", "default/props.conf"})
        self.assertFalse(
            any(name.startswith(("bin/", "lib/", "appserver/")) for name in files)
        )
        for section in conf(files["default/props.conf"]).values():
            self.assertFalse(
                any(
                    key.startswith(
                        ("LOOKUP-", "REPORT-", "EVAL-", "TRANSFORMS-", "RULESET-")
                    )
                    for key in section
                )
            )
            self.assertNotIn("INDEXED_EXTRACTIONS", section)
        inputs = conf(files["README/examples/inputs-hf.conf.example"])
        self.assertTrue(inputs.sections())
        for name in inputs.sections():
            self.assertEqual(inputs[name]["disabled"], "1")

    def test_native_boundaries_preserve_multiline_and_separate_events(self):
        props = conf(payload()["default/props.conf"])
        headers = [
            "<14>1 2026-09-16T12:00:00.000Z vc01 vpxd - - - ",
            "2026-09-16T12:00:00Z vc01 vpxd ",
            "<14>Sep 16 12:00:00 vc01 vpxd ",
            "Sep 16 12:00:00 vc01 vpxd ",
            "",
        ]
        for kind in ("vcenter", "aria", "esxi"):
            expression = props["vmware:vision:" + kind]["LINE_BREAKER"]
            for header in headers:
                first = header + "Event [1] changed: cpu=4\n memory=8192"
                second = header + "Event [2] powered on"
                raw = first + "\r\n" + second
                matches = list(re.finditer(expression, raw))
                self.assertEqual(len(matches), 1, (kind, header))
                self.assertEqual(raw[: matches[0].start(1)], first)
                self.assertEqual(raw[matches[0].end(1) :], second)

    def test_json_lines_and_timestamp_prefix(self):
        props = conf(payload()["default/props.conf"])["vmware:vision:json"]
        raw = '{"createdTime":"2026-09-16T12:00:00Z","message":"a\\nb"}\n{"timestamp":"2026-09-16T12:01:00Z"}'
        self.assertEqual(len(list(re.finditer(props["LINE_BREAKER"], raw))), 1)
        timestamp = re.search(props["TIME_PREFIX"], raw)
        self.assertIsNotNone(timestamp)
        self.assertTrue(raw[timestamp.end() :].startswith("2026-09-16T12:00:00Z"))

    def test_archive_is_reproducible_and_safe_for_linux_installation(self):
        files = payload()
        content = archive(files)
        self.assertEqual(content, archive(files))
        with tarfile.open(fileobj=io.BytesIO(content), mode="r:gz") as package:
            archived = {}
            for member in package.getmembers():
                self.assertTrue(
                    member.name.startswith(APP_ID + "/") or member.name == APP_ID
                )
                self.assertNotIn("..", Path(member.name).parts)
                self.assertNotIn("\\", member.name)
                self.assertFalse(member.issym() or member.islnk())
                self.assertEqual(member.mode, 0o755 if member.isdir() else 0o644)
                if member.isfile():
                    archived[member.name[len(APP_ID) + 1 :]] = package.extractfile(
                        member
                    ).read()
            self.assertEqual(archived, files)

    def test_index_replication_is_only_in_cluster_example(self):
        files = payload()
        standalone = conf(files["README/examples/indexes-indexer.conf.example"])
        cluster = conf(files["README/examples/indexes-cluster.conf.example"])
        self.assertNotIn("repFactor", standalone["vmware"])
        self.assertEqual(cluster["vmware"]["repFactor"], "auto")


if __name__ == "__main__":
    unittest.main()
