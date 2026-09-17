"""Static dashboard contracts; live SPL validation remains a separate check."""

import configparser
import json
from pathlib import Path
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from dashboard_queries import resolve_search, isolated_query


class DashboardContracts(unittest.TestCase):
    def test_overview_uses_five_dispatches_and_same_event_latest_row(self):
        form = ET.parse(ROOT / "package/default/data/ui/views/overview.xml").getroot()
        self.assertEqual(len(form.findall(".//search/query")), 11)
        self.assertEqual(sum(not s.get("base") for s in form.findall(".//search")), 5)
        latest = next(
            p
            for p in form.findall(".//panel")
            if p.findtext(".//title") == "Latest VM activity"
        )
        query = latest.findtext(".//query")
        self.assertIn("dedup vm_key", query)
        self.assertNotIn("latest(", query)
        self.assertIn("`vmware_vision_audit`", query)

    def test_postprocess_queries_resolve_to_transforming_bases(self):
        for path in (ROOT / "package/default/data/ui/views").glob("*.xml"):
            form = ET.parse(path).getroot()
            for search in form.findall(".//search"):
                if not search.get("base"):
                    continue
                base = next(
                    s
                    for s in form.findall(".//search")
                    if s.get("id") == search.get("base")
                )
                self.assertRegex(base.findtext("query"), r"\b(?:stats|tstats)\b")
                query = resolve_search(form, search)
                self.assertNotIn("$vc|s$", isolated_query(query, "index=isolated_test"))

    def test_coverage_chart_pivots_format_and_limits_identity_scope(self):
        form = ET.parse(ROOT / "package/default/data/ui/views/coverage.xml").getroot()
        queries = {
            p.findtext(".//title"): p.findtext(".//query")
            for p in form.findall(".//panel")
        }
        self.assertEqual(
            queries["Parser coverage"],
            "chart sum(events) over parser_status by parser_format",
        )
        self.assertIn("match(event_type", queries["VM event identity quality"])
        self.assertIn("`vmware_vision_audit`", queries["VM event identity quality"])

    def test_acceleration_is_explicit_and_excludes_free_text(self):
        config = configparser.ConfigParser()
        config.read(ROOT / "package/default/datamodels.conf")
        self.assertEqual(config["VMware_Vision_Activity"]["acceleration"], "false")
        model = json.loads(
            (
                ROOT / "package/default/data/models/VMware_Vision_Activity.json"
            ).read_text()
        )
        names = {f["fieldName"] for f in model["objects"][0]["fields"]}
        self.assertFalse({"message", "change_details", "event_uid", "vm_key"} & names)
        view = ET.parse(
            ROOT / "package/default/data/ui/views/accelerated_activity.xml"
        ).getroot()
        self.assertEqual(view.find("fieldset").get("autoRun"), "false")
        self.assertIn("summariesonly=true", view.find("search/query").text)
        self.assertIn("unsummarized", view.findtext("description"))

    def test_candidate_filter_keeps_supported_event_shapes(self):
        config = configparser.ConfigParser(interpolation=None)
        config.read(ROOT / "package/default/macros.conf")
        definition = config["vmware_vision_audit"]["definition"]
        expression = re.search(r'regex _raw="(.*)" \| search', definition)[1].replace(
            r"\"", '"'
        )
        for raw in [
            "Event [42] [...",
            "vim.event.VmCreatedEvent",
            "eventType=VmCreatedEvent",
            '{"event_type":"VmCreatedEvent"}',
            '{"type":"VmCreatedEvent"}',
            "type=VmCreatedEvent",
            '{"_typeName":"VmCreatedEvent"}',
        ]:
            self.assertIsNotNone(re.search(expression, raw), raw)
        self.assertIsNone(
            re.search(expression, "user: com.vmware.vim.eam [VpxLRO] -- FINISH lro-13")
        )
