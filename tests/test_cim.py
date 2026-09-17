"""CIM semantics, exclusion boundaries and dashboard migration regressions."""

import configparser
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "package/bin"))
from vmware_vision_parser import EVENTS, parse
from vmware_vision_cim import CHANGE_TYPES
from test_parser import event


class CimMappings(unittest.TestCase):
    def test_native_action_preserved_for_every_event_class(self):
        for kind, spec in EVENTS.items():
            result = parse(event(kind, "Recorded event"))
            self.assertEqual(result["vmware_action"], spec[0], kind)

    def test_login_outcomes_and_source(self):
        for kind, action in [
            ("UserLoginSessionEvent", "success"),
            ("BadUsernameSessionEvent", "failure"),
            ("InvalidLogin", "failure"),
        ]:
            r = parse(event(kind, "User LAB\\alice@192.0.2.4 logged in"))
            self.assertEqual(
                (r["cim_dataset"], r["action"], r["src"], r["dest"]),
                ("Authentication", action, "192.0.2.4", "vc01.example"),
            )
            self.assertEqual(r["user"], "LAB\\alice")
        r = parse("eventType=UserLoginSessionEvent status=failed")
        self.assertEqual(r["action"], "failure")

    def test_excluded_events_do_not_enter_cim(self):
        for kind in [
            "UserLogoutSessionEvent",
            "VmStartingEvent",
            "VmResettingEvent",
            "TaskEvent",
            "AlarmStatusChangedEvent",
            "HostConnectedEvent",
            "FutureEvent",
            "PermissionUpdatedEvent",
            "RoleAddedEvent",
        ]:
            self.assertEqual(
                parse(event(kind, "Recorded event"))["cim_dataset"], "", kind
            )
        self.assertEqual(
            parse("vpxd[42] [Originator@6876] query completed")["cim_dataset"], ""
        )

    def test_failed_change_is_attempt_not_completed_state(self):
        r = parse(
            "eventType=VmFailedToPowerOnEvent vm_name=app01 vm_id=vm-42 vcenter=vc01 user=alice"
        )
        self.assertEqual(
            (r["action"], r["status"], r["observed_state"]), ("started", "failure", "")
        )
        self.assertEqual(
            (r["object"], r["object_id"], r["object_category"]),
            ("app01", "vm-42", "virtual_machine"),
        )
        self.assertEqual(
            (r["cim_dataset"], r["vmware_action"]), ("Change", "power_failed")
        )

    def test_missing_values_not_invented(self):
        r = parse("eventType=VmReconfiguredEvent vcenter=vc01")
        for field in ["object", "object_id", "object_attrs", "src", "command", "user"]:
            self.assertEqual(r[field], "", field)
        self.assertEqual(parse("eventType=UserLoginSessionEvent")["src"], "")

    def test_snapshot_is_change_to_vm_not_fabricated_snapshot_identity(self):
        r = parse("eventType=VmSnapshotTakenEvent vm_name=app01 vm_id=vm-42")
        self.assertEqual(
            (r["action"], r["change_type"], r["object_category"]),
            ("modified", "snapshot", "virtual_machine"),
        )
        self.assertEqual(r["vmware_action"], "snapshot_created")

    def test_explicit_change_allowlist_uses_supported_cim_actions(self):
        for kind in CHANGE_TYPES:
            r = parse(event(kind, "Recorded event"))
            self.assertEqual(r["cim_dataset"], "Change", kind)
            self.assertIn(r["status"], ["success", "failure"])
            self.assertIn(
                r["action"],
                ["created", "deleted", "modified", "started", "stopped", "restarted"],
            )

    def test_cim_tags_visible_outside_app(self):
        c = configparser.ConfigParser(interpolation=None)
        c.read_string(
            (ROOT / "package/metadata/default.meta")
            .read_text()
            .replace("[]", "[defaults]")
        )
        for name in ["vmware_vision_authentication", "vmware_vision_change"]:
            for path in ["eventtypes/" + name, "tags/eventtype=" + name]:
                self.assertEqual(c[path]["export"], "system")
        tags = configparser.ConfigParser()
        tags.read(ROOT / "package/default/tags.conf")
        self.assertEqual(
            tags["eventtype=vmware_vision_authentication"]["authentication"], "enabled"
        )
        self.assertEqual(tags["eventtype=vmware_vision_change"]["change"], "enabled")

    def test_generated_values_are_not_required_in_raw_event_index(self):
        fields = configparser.ConfigParser()
        fields.read(ROOT / "package/default/fields.conf")
        # Without this, tag/model constraints silently reject rows before lookup execution.
        for field in [
            "action",
            "status",
            "cim_dataset",
            "record_kind",
            "parser_status",
            "vmware_action",
            "vm_key",
            "app",
            "change_type",
        ]:
            self.assertEqual(fields[field]["INDEXED_VALUE"], "false", field)
            self.assertNotIn("INDEXED", fields[field])

    def test_bundled_dashboard_queries_keep_native_actions(self):
        for p in (ROOT / "package/default/data/ui/views").glob("*.xml"):
            self.assertIsNone(re.search(r"\baction\b", p.read_text()), p.name)
        model = json.loads(
            (
                ROOT / "package/default/data/models/VMware_Vision_Activity.json"
            ).read_text()
        )
        names = {f["fieldName"] for f in model["objects"][0]["fields"]}
        self.assertIn("vmware_action", names)
        self.assertNotIn("action", names)
