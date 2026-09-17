import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "package/bin"))
from vmware_vision_parser import EVENTS, parse


def event(kind, message, severity="info", user="LAB\\alice", key=101):
    return f"<14>1 2026-09-14T12:00:00.123Z vc01.example vpxd 123 - - Event [{key}] [1-1] [2026-09-14T12:00:00.123Z] [vim.event.{kind}] [{severity}] [{user}] [DC1] [{key}] [{message}]"


class ParserTests(unittest.TestCase):
    def test_bracket_header_and_power(self):
        result = parse(
            event(
                "VmPoweredOnEvent",
                "Virtual machine app01 on esx01 in DC1 is powered on",
            ),
            "relay",
        )
        self.assertEqual(
            (
                result["vm_name"],
                result["user"],
                result["vcenter"],
                result["observed_state"],
            ),
            ("app01", "LAB\\alice", "vc01.example", "powered_on"),
        )

    def test_created(self):
        self.assertEqual(
            parse(
                event("VmCreatedEvent", "Created virtual machine app01 on esx01 in DC1")
            )["vm_name"],
            "app01",
        )

    def test_vm_names_with_spaces(self):
        self.assertEqual(
            parse(
                event("VmRemovedEvent", "Virtual machine Finance SQL 01 was removed")
            )["vm_name"],
            "Finance SQL 01",
        )

    def test_reconfiguration_multiline(self):
        r = parse(
            event(
                "VmReconfiguredEvent",
                "Reconfigured app01 on esx01 in DC1. Changed: config.hardware.numCPU: 2 -> 4;\nconfig.hardware.memoryMB: 4096 -> 8192",
            )
        )
        self.assertEqual(r["vm_name"], "app01")
        self.assertIn("memoryMB", r["change_fields"])
        self.assertIn("4096", r["change_details"])

    def test_json_identity_and_changes(self):
        r = parse(
            json.dumps(
                {
                    "eventType": "VmReconfiguredEvent",
                    "vm": {"name": "app01", "vm": {"value": "vm-42"}},
                    "vcenter": "vc01",
                    "userName": "alice",
                    "configSpec": {"numCPUs": 4},
                    "fullFormattedMessage": "Reconfigured app01",
                }
            )
        )
        self.assertEqual(r["vm_key"], "vc01::vm-42")
        self.assertEqual(r["change_fields"], "numCPUs")

    def test_aria_json_envelope(self):
        r = parse(
            json.dumps(
                {
                    "text": event(
                        "VmPoweredOffEvent", "Virtual machine app01 is powered off"
                    ),
                    "fields": [{"name": "vm_id", "content": "vm-42"}],
                }
            ),
            "aria-relay",
        )
        self.assertEqual(r["vm_id"], "vm-42")
        self.assertEqual(r["vcenter"], "vc01.example")

    def test_requested_is_never_observed_power(self):
        for kind in [
            "VmStartingEvent",
            "VmStoppingEvent",
            "VmResettingEvent",
            "VmGuestShutdownEvent",
        ]:
            r = parse(event(kind, "Virtual machine app01 operation requested"))
            self.assertEqual(r["status"], "requested")
            self.assertEqual(r["observed_state"], "")

    def test_failed_power_does_not_set_state(self):
        r = parse(event("VmFailedToPowerOnEvent", "Cannot power on app01", "error"))
        self.assertEqual((r["status"], r["observed_state"]), ("failure", ""))

    def test_unknown_event_does_not_infer_success_from_message(self):
        r = parse(event("FutureVendorEvent", "Virtual machine app01 powered on"))
        self.assertEqual(
            (r["parser_status"], r["status"], r["observed_state"]),
            ("unmapped_event_type", "unknown", ""),
        )

    def test_no_type_text_is_not_a_completed_event(self):
        r = parse("Power on request failed for virtual machine app01")
        self.assertEqual(r["action"], "unknown")

    def test_quoted_key_value(self):
        r = parse(
            'eventType=VmReconfiguredEvent vm_name="Finance SQL" vm_id=vm-12 user="LAB\\alice" vcenter=vc01'
        )
        self.assertEqual((r["vm_name"], r["vm_key"]), ("Finance SQL", "vc01::vm-12"))

    def test_uuid_precedes_name(self):
        r = parse(json.dumps({"vm_uuid": "abcd", "vm_name": "old", "vcenter": "vc01"}))
        s = parse(json.dumps({"vm_uuid": "abcd", "vm_name": "new", "vcenter": "vc01"}))
        self.assertEqual(r["vm_key"], s["vm_key"])

    def test_same_name_on_different_vcenters(self):
        a = parse("vm_name=app01 vcenter=vc01")
        b = parse("vm_name=app01 vcenter=vc02")
        self.assertNotEqual(a["vm_key"], b["vm_key"])

    def test_dedup_source_scoped(self):
        a = parse(event("VmCreatedEvent", "Created app01"))
        b = parse(
            event("VmCreatedEvent", "Created app01").replace(
                "vc01.example", "vc02.example"
            )
        )
        self.assertNotEqual(a["event_uid"], b["event_uid"])

    def test_login(self):
        r = parse(event("UserLoginSessionEvent", "User LAB\\alice@10.1.2.3 logged in"))
        self.assertEqual((r["category"], r["src_ip"]), ("authentication", "10.1.2.3"))

    def test_empty_user(self):
        r = parse(event("VmCreatedEvent", "Created app01", user=""))
        self.assertEqual(r["user"], "")

    def test_task_failure(self):
        r = parse(
            json.dumps(
                {"eventType": "TaskEvent", "info": {"state": "error", "key": "task-1"}}
            )
        )
        self.assertEqual((r["status"], r["task_id"]), ("failure", "task-1"))

    def test_alarm_severity_is_not_failed_operation(self):
        r = parse(
            event(
                "AlarmStatusChangedEvent",
                "Alarm changed from green to red",
                severity="error",
            )
        )
        self.assertEqual((r["severity"], r["status"]), ("error", "observed"))

    def test_unregistered_is_not_deleted(self):
        result = parse(event("VmUnregisteredEvent", "Unregistered app01"))
        self.assertEqual(result["vmware_action"], "unregistered")
        self.assertEqual(result["action"], "modified")

    def test_output_preserves_special_characters(self):
        message = 'Reconfigured app01: Changed: annotation="a,b & <xml>"'
        raw = event("VmReconfiguredEvent", message)
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=["_raw", "host", "sourcetype"])
        writer.writeheader()
        writer.writerow(
            {"_raw": raw, "host": "vc01", "sourcetype": "vmware:vision:vcenter"}
        )
        output = subprocess.run(
            [sys.executable, str(ROOT / "package/bin/vmware_lookup.py")],
            input=buffer.getvalue(),
            capture_output=True,
            text=True,
            check=True,
        )
        row = next(csv.DictReader(io.StringIO(output.stdout)))
        self.assertEqual(row["message"], message)
        self.assertEqual(row["_raw"], raw)

    def test_all_mapping_states_are_conservative(self):
        for kind, (_, _, status, state) in EVENTS.items():
            if status != "success":
                self.assertFalse(state, kind)

    def test_malformed_payloads_do_not_crash(self):
        for raw in [
            "",
            "{bad json",
            "[]",
            "null",
            "<14>1 - - - - - -",
            '{"vm":{"vm":null}}',
        ]:
            self.assertIn("parser_status", parse(raw))


if __name__ == "__main__":
    unittest.main()
